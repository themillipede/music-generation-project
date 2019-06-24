import json
import numpy as np
import tensorflow as tf
from tensorflow import contrib
tfe = contrib.eager
tf.enable_eager_execution()

from definitions import note_name_idx
from note_parsing import Melody
from chord_parsing import ChordProgression
from bar_parsing import BarSequence
from timesteps import Piece

from Model import model

NUM_EPOCHS = 100
CHECKPOINT_DIR = "/tmp/music-generation"
CHECKPOINT_EVERY = 10


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
        melody = Melody(details['notes'], 'PitchMIDI/' + title + '_pitches' + '.MID')
        chords = ChordProgression(details['chords'])
        bars = BarSequence(eval(details['bars']))
        piece = Piece(title, details['composer'], details['pickup'], melody.melody, chords.chords, bars.bars)
        vectors = timestep_vectors(piece.timesteps)
        vectors = vectors.astype(np.float32)
        yield vectors


ds = tf.data.Dataset.from_generator(
    data, tf.float32, tf.TensorShape([None, 100])
)
# ds = ds.map(lambda v: tf.split(v, [38, 13, 13, 12, 24], axis=1))
ds = ds.map(lambda v: tf.expand_dims(v, 0)) # add dummy batch dimension: [batch_size, num_timesteps, 100]

# def shift_output_by_one_timestep(v):
#     return tf.pad(v[:, 1:, :], [[0, 0], [0, 1], [0, 0]])

def shift_input_by_one_timestep(v):
    return tf.pad(v[:, :-1, :], [[0, 0], [1, 0], [0, 0]])

def loss(v):
    v_in = shift_input_by_one_timestep(v)
    logits_p, logits_r, logits_b, logits_c, logits_d = model.split_vectors(model.build_model(v_in))
    targets_p, targets_r, targets_b, targets_c, targets_d = model.split_vectors(v)

    loss_p = tf.nn.softmax_cross_entropy_with_logits_v2(labels=targets_p, logits=logits_p)
    loss_r = tf.nn.softmax_cross_entropy_with_logits_v2(labels=targets_r, logits=logits_r)
    loss_b = tf.nn.softmax_cross_entropy_with_logits_v2(labels=targets_b, logits=logits_b)
    loss_d = tf.nn.softmax_cross_entropy_with_logits_v2(labels=targets_d, logits=logits_d)

    loss_c = tf.nn.sigmoid_cross_entropy_with_logits(labels=targets_c, logits=logits_c)
    loss_c = tf.reduce_sum(loss_c, axis=-1)

    return tf.reduce_mean(loss_p + loss_r + loss_b + loss_d + loss_c)

def grad(v):
    with tf.GradientTape() as tape:
        loss_value = loss(v)
    return loss_value, tape.gradient(loss_value, tf.trainable_variables())

optimizer = tf.train.AdamOptimizer(learning_rate=2e-4)
# optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.01)
global_step = tf.Variable(0)

# set up checkpointing
ckpt = tf.train.Checkpoint()
ckpt.optimizer = optimizer
ckpt.step = global_step
ckpt.vars = tf.trainable_variables()
ckpt_manager = tf.train.CheckpointManager(ckpt, CHECKPOINT_DIR, max_to_keep=3)

# # code below can be used to restore from checkpoints
# if ckpt_manager.latest_checkpoint:
#     ckpt.restore(ckpt_manager.latest_checkpoint)
#     print("Restored from {}".format(ckpt_manager.latest_checkpoint))
# else:
#     print("Initializing from scratch.")

for epoch in range(NUM_EPOCHS):
    epoch_loss_avg = tfe.metrics.Mean()
    for v in ds:
        loss_value, grads = grad(v)
        optimizer.apply_gradients(zip(grads, tf.trainable_variables()), global_step)
        epoch_loss_avg(loss_value)

    print("Epoch %d/%d: loss = %.4f" % (epoch + 1, NUM_EPOCHS, epoch_loss_avg.result()))

    if (epoch + 1) % CHECKPOINT_EVERY == 0:
        ckpt_path = ckpt_manager.save()
        print("  checkpoint saved to %s" % ckpt_path)

# 100 epochs with NUM_HIDDENS=256: 7.7758
# 100 epochs without LSTM: 11.1428
# 100 epochs without LSTM, self-prediction: 9.5903





