import numpy as np
import tensorflow as tf
from tensorflow import contrib
tfe = contrib.eager
tf.enable_eager_execution()

from Model import model

CHECKPOINT_DIR = "/tmp/music-generation"
NUM_SAMPLE_STEPS = 50

# build model to enable loading up the checkpoint
# TODO: find a cleaner way to handle this
_ = model.build_model(np.zeros([1, 1, 100], dtype=np.float32))

# set up checkpointing
ckpt = tf.train.Checkpoint()
ckpt.vars = tf.trainable_variables()
ckpt_manager = tf.train.CheckpointManager(ckpt, CHECKPOINT_DIR, max_to_keep=3)

# restore from checkpoint
if not ckpt_manager.latest_checkpoint:
    raise RuntimeError("No valid checkpoint found!")

ckpt.restore(ckpt_manager.latest_checkpoint)
print("Restored from {}".format(ckpt_manager.latest_checkpoint))

state = model.initial_state_for_sampling()
sample = tf.constant(np.zeros([1, 100]), dtype=tf.float32)

samples = []

for s in range(NUM_SAMPLE_STEPS):
    print("Sampling step %d/%d" % (s + 1, NUM_SAMPLE_STEPS))
    sample, state = model.build_model_for_sampling(sample, state)
    samples.append(sample)

samples = np.array(samples)  # stack along the time dimension
samples = np.transpose(samples, [1, 0, 2])  # reorder axes to [batch, timesteps, channels]

import pdb; pdb.set_trace()

# TODO: add code to store samples
# e.g. np.save("path/to/samples.npy", samples)