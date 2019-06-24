import tensorflow as tf
import sonnet as snt

NUM_HIDDEN_UNITS = 256 # 64
BATCH_SIZE = 1  # for now, we use batch size 1 because we have variable-length sequences.

def split_vectors(v):
    return tf.split(v, [38, 13, 13, 12, 24], axis=-1)

cell = snt.LSTM(NUM_HIDDEN_UNITS)
initial_state = cell.initial_state(BATCH_SIZE)
output_module = snt.Linear(100)
batch_output_module = snt.BatchApply(output_module)

def build_model(v):
    h, final_state = tf.nn.dynamic_rnn(cell=cell, inputs=v, initial_state=initial_state)
    return batch_output_module(h) # [batch_size, num_timesteps, 100]

def initial_state_for_sampling():
    return initial_state

def build_model_for_sampling(v, prev_state):
    h, next_state = cell(v, prev_state)
    y = output_module(h)
    s = sample(y)
    return s, next_state

def sample(y):
    p, r, b, c, d = split_vectors(y)
    sp = tf.one_hot(tf.distributions.Categorical(logits=p).sample(), depth=38, dtype=tf.float32)
    sr = tf.one_hot(tf.distributions.Categorical(logits=r).sample(), depth=13, dtype=tf.float32)
    sb = tf.one_hot(tf.distributions.Categorical(logits=b).sample(), depth=13, dtype=tf.float32)
    sc = tf.cast(tf.distributions.Bernoulli(logits=c).sample(), tf.float32)
    sd = tf.one_hot(tf.distributions.Categorical(logits=d).sample(), depth=24, dtype=tf.float32)
    return tf.concat([sp, sr, sb, sc, sd], axis=-1)