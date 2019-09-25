import json
import numpy as np
import tensorflow as tf
import os

from definitions import note_name_idx
from note_parsing import Melody
from chord_parsing import ChordProgression
from bar_parsing import BarSequence
from timesteps import Piece

# from Model import model
from Model import model_autoregressive as model

NUM_UPDATES = 10000
REPORT_EVERY = 10  # How often loss is reported.
CHECKPOINT_EVERY = 100  # How often a checkpoint is created.
CHECKPOINT_DIR = "checkpoints"
SUMMARIES_DIR = "summaries"  # Summaries for TensorBoard.


# TODO: train/test split


def timestep_vectors(piece):
    pitch = np.eye(38, dtype=int)[
        [36 if ts.same_note else ts.note_pitch - 48 if ts.note_pitch > 0 else 37 for ts in piece]
    ]
    root = np.eye(13, dtype=int)[[note_name_idx[ts.root] if ts.root else 12 for ts in piece]]
    bass = np.eye(13, dtype=int)[[note_name_idx[ts.bass] if ts.bass else 12 for ts in piece]]
    chord = np.array([[i in ts.full_chordset for i in range(12)] for ts in piece], dtype=int)
    duration = np.eye(24, dtype=int)[[int(ts.duration / 10 - 1) for ts in piece]]
    return np.concatenate([pitch, root, bass, chord, duration], axis=1)


with open('test_data.json') as f:
    piece_data = json.load(f)


def data():
    for title, details in piece_data.items():
        if not details["chords"]:
            continue
        midi_filename = 'PitchMIDI/' + title + '_pitches' + '.MID'
        melody = Melody.from_duration_list_and_pitch_midi(details['notes'], midi_filename)
        chords = ChordProgression(details['chords'])
        bars = BarSequence(eval(details['bars']))
        piece = Piece(title, details['composer'], details['pickup'], melody.melody, chords.chords, bars.bars)
        vectors = timestep_vectors(piece.timesteps)
        vectors = vectors.astype(np.float32)  # Convert to single-precision floats.
        yield vectors


ds = tf.data.Dataset.from_generator(data, tf.float32, [None, 100])  # Convert generator into tf dataset.
ds = ds.repeat()  # Cycle through the data indefinitely.
ds = ds.shuffle(buffer_size=256)  # Shuffle the examples.
ds = ds.map(lambda v: {'data': v, 'length': tf.shape(v)[0]})  # Keep track of lengths (for tf.nn.dynamic_rnn).
ds = ds.padded_batch(
    model.BATCH_SIZE,
    {'data': [None, 100], 'length': []},  # Pads each piece to length of longest.
    #drop_remainder=True,  # Unnecessary because dataset loops indefinitely.
)  # Create padded batches (pad to max. sequence length in batch).

iterator = ds.make_one_shot_iterator()
inputs = iterator.get_next()


def get_loss(inputs):
    v = inputs['data']  # Tensor of shape [batch_size, num_timesteps, 100].
    lengths = inputs['length']  # Vector of length batch_size.

    outputs = model.build_model(v, lengths)  # Logits of different timestep components.
    logits_p, logits_r, logits_b, logits_c, logits_d = model.split_vectors(outputs)
    targets_p, targets_r, targets_b, targets_c, targets_d = model.split_vectors(v)

    # Get loss for each timestep in each piece: [batch_size, num_timesteps].
    loss_p = tf.nn.softmax_cross_entropy_with_logits_v2(labels=targets_p, logits=logits_p)
    loss_r = tf.nn.softmax_cross_entropy_with_logits_v2(labels=targets_r, logits=logits_r)
    loss_b = tf.nn.softmax_cross_entropy_with_logits_v2(labels=targets_b, logits=logits_b)
    loss_d = tf.nn.softmax_cross_entropy_with_logits_v2(labels=targets_d, logits=logits_d)

    # Get loss for each chord note in each timestep in each piece: [batch_size, num_timesteps, 12].
    loss_c = tf.nn.sigmoid_cross_entropy_with_logits(labels=targets_c, logits=logits_c)
    # Sum losses over all the chord notes: [batch_size, num_timesteps].
    loss_c = tf.reduce_sum(loss_c, axis=-1)

    # Get the mean loss over all axes.
    return tf.reduce_mean(loss_p + loss_r + loss_b + loss_d + loss_c)


loss = get_loss(inputs)
optimizer = tf.train.AdamOptimizer(learning_rate=2e-4)
# optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.01)
step = tf.train.get_or_create_global_step()  # Keeps track of the current training step.
train_op = optimizer.minimize(loss, step)

### TRAINING LOOP
saver = tf.train.Saver(
    tf.global_variables(),  # Save all tf variables (e.g. model weights, biases, global step).
    max_to_keep=5,  # Maximum number of checkpoints to keep around.
    save_relative_paths=True
)

sess = tf.Session()

# Restore from checkpoint if available.
ckpt_path = tf.train.latest_checkpoint(CHECKPOINT_DIR)

if ckpt_path is None:
    print("No valid checkpoints found, initializing variables from scratch")
    sess.run(tf.global_variables_initializer())  # Initialize all the variables.
else:
    print("Restoring variables from checkpoint: %s" % ckpt_path)
    saver.restore(sess, ckpt_path)

# Set up summaries for TensorBoard.
summary_writer = tf.summary.FileWriter(SUMMARIES_DIR)

avg_loss = 0

while True:
    i, loss_value, _ = sess.run([step, loss, train_op])
    avg_loss += loss_value / float(REPORT_EVERY)

    if (i + 1) % REPORT_EVERY == 0:
        print ("Step %d: loss = %.4f" % (i + 1, avg_loss))
        summary = tf.Summary()
        summary.value.add(tag="loss", simple_value=avg_loss)
        summary_writer.add_summary(summary, i)
        avg_loss = 0

    if (i + 1) % CHECKPOINT_EVERY == 0:
        ckpt_path = saver.save(sess, os.path.join(CHECKPOINT_DIR, "model"), global_step=step)
        print("Step %d: checkpoint saved to %s" % (i + 1, ckpt_path))

    if (i + 1) >= NUM_UPDATES:
        print("Stopping training after %d steps." % NUM_UPDATES)
        break
