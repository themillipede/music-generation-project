import tensorflow as tf
import sonnet as snt
import numpy as np

NUM_LSTM_UNITS = 256
BATCH_SIZE = 32


def split_vectors(v):
    return tf.split(v, [38, 13, 13, 12, 24], axis=-1)


def shift_by_one_timestep(v):
    # Shift in time: chop off the last vector and add a vector of zeroes at the front.
    return tf.pad(v[:, :-1, :], [[0, 0], [1, 0], [0, 0]])


cell = snt.LSTM(NUM_LSTM_UNITS)
initial_state = cell.initial_state(BATCH_SIZE)


def output_net(num_hidden_layers, num_hidden_units, num_outputs, inputs):
    h = tf.concat(inputs, axis=-1)  # Combine all inputs into one.

    for _ in range(num_hidden_layers):
        h = snt.Conv1D(num_hidden_units, kernel_shape=1)(h)
        h = tf.nn.relu(h)

    return snt.Conv1D(num_outputs, kernel_shape=1)(h)


# Compute mask for autoregressive masking like in PixelCNN.
def create_mask(num_inputs, num_outputs, num_channels, mask_self=False):
    assert num_inputs % num_channels == 0
    assert num_outputs % num_channels == 0

    num_inputs_per_channel = num_inputs // num_channels
    num_outputs_per_channel = num_outputs // num_channels
    mask = np.zeros([num_inputs, num_outputs], dtype=np.float32)

    for i in range(num_channels):
        # Connect the outputs for channel i to all preceding inputs.
        num_visible_input_channels = i if mask_self else i + 1
        # Connect all visible input units to the output units in the current channel.
        mask[0:num_visible_input_channels * num_inputs_per_channel,
             i * num_outputs_per_channel:(i + 1) * num_outputs_per_channel] = 1.0

    return mask.reshape(1, num_inputs, num_outputs)  # Add batch axis.


# Constructs a masked output network (used for chords notes).
def masked_output_net(num_hidden_layers, num_hidden_units, num_outputs, masked_input, other_inputs):
    assert num_hidden_layers >= 1
    mask_in = create_mask(num_outputs, num_hidden_units, num_outputs, mask_self=True)
    mask_hidden = create_mask(num_hidden_units, num_hidden_units, num_outputs)
    mask_out = create_mask(num_hidden_units, num_outputs, num_outputs)

    # First hidden layer.
    h = tf.concat(other_inputs, axis=-1)  # Combine all other (unmasked) inputs into one.
    h = snt.Conv1D(num_hidden_units, kernel_shape=1)(h)  # Apply unmasked linear layer.
    # Apply masked linear layer to masked input and add to hidden layer activation.
    h += snt.Conv1D(num_hidden_units, kernel_shape=1, mask=mask_in)(masked_input)
    h = tf.nn.relu(h)  # Apply ReLU to combined activation.

    # Other hidden layers.
    for _ in range(num_hidden_layers - 1):
        h = snt.Conv1D(num_hidden_units, kernel_shape=1, mask=mask_hidden)(h)
        h = tf.nn.relu(h)

    return snt.Conv1D(num_outputs, kernel_shape=1, mask=mask_out)(h)


# Set up autoregressive output modules.
p_module = snt.Module(lambda inputs: output_net(1, 128, 38, inputs), name='p_module')
r_module = snt.Module(lambda inputs: output_net(1, 128, 13, inputs), name='r_module')
b_module = snt.Module(lambda inputs: output_net(1, 128, 13, inputs), name='b_module')
c_module = snt.Module(lambda m, other_inputs: masked_output_net(1, 384, 12, m, other_inputs), name='c_module')
d_module = snt.Module(lambda inputs: output_net(1, 128, 24, inputs), name='d_module')


def build_model(v, lengths):
    v_in = shift_by_one_timestep(v)
    h, final_state = tf.nn.dynamic_rnn(
        cell=cell,
        inputs=v_in,
        initial_state=initial_state,
        sequence_length=lengths
    )

    # Autoregressive output networks.
    p, r, b, c, d = split_vectors(v)

    p_out = p_module([h])
    r_out = r_module([h, p])
    b_out = b_module([h, p, r])
    c_out = c_module(c, [h, p, r, b])  # Also gets itself as input!
    d_out = d_module([h, p, r, b, c])

    # Join all the outputs and return.
    return tf.concat([p_out, r_out, b_out, c_out, d_out], axis=-1)


def initial_state_for_sampling():
    return initial_state


def build_model_for_sampling(v, prev_state):
    h, next_state = cell(v, prev_state)
    h = tf.expand_dims(h, 1)  # Add time axis, because the output nets operate on 3D tensors (containing sequences).

    p = sample_categorical(p_module([h]))
    r = sample_categorical(r_module([h, p]))
    b = sample_categorical(b_module([h, p, r]))

    # Sample c repeatedly and select the correct parts.
    # TODO: tf.while_loop?
    c = tf.zeros([BATCH_SIZE, 1, 12], dtype=tf.float32)
    for i in range(12):
        c_new = sample_bernoulli(c_module(c, [h, p, r, b]))
        c = tf.concat([c[:, :, :i], c_new[:, :, i:]], axis=-1)  # keep the previously sampled steps

    d = sample_categorical(d_module([h, p, r, b, c]))

    s = tf.concat([p, r, b, c, d], axis=-1)  # Join the parts together in a single vector.
    s = tf.squeeze(s, axis=1)  # Remove time axis.
    return s, next_state


def sample_categorical(logits):
    num_outputs = logits.shape.as_list()[-1]
    y = tf.distributions.Categorical(logits=logits).sample()
    return tf.one_hot(y, depth=num_outputs, dtype=tf.float32)


def sample_bernoulli(logits):
    return tf.cast(tf.distributions.Bernoulli(logits=logits).sample(), tf.float32)

# p: pitch
# r: root
# b: bass
# c: chord notes (bernoulli)
# d: duration
