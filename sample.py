import numpy as np
import tensorflow as tf

# from Model import model
from Model import model_autoregressive as model

OUTPUT_PATH = "samples.npy"
CHECKPOINT_DIR = "checkpoints"  # Needs to load up checkpoint from a trained model.
NUM_SAMPLE_STEPS = 100


step = tf.train.get_or_create_global_step()  # TODO: get rid of this -- not needed?

state = model.initial_state_for_sampling()
sample = tf.constant(np.zeros([model.BATCH_SIZE, 100]), dtype=tf.float32)  # Empty timestep vector.
samples = []

for i in range(NUM_SAMPLE_STEPS):
    # TODO: tf.while_loop?
    sample, state = model.build_model_for_sampling(sample, state)
    samples.append(sample)

samples = tf.stack(samples, axis=1)  # Stack into single tensor of shape [batch_size, num_timesteps, 100].

saver = tf.train.Saver(tf.global_variables(), save_relative_paths=True)

sess = tf.Session()

ckpt_path = tf.train.latest_checkpoint(CHECKPOINT_DIR)

if ckpt_path is None:
    raise RuntimeError("No valid checkpoint found!")

print("Restoring variables from checkpoint: %s" % ckpt_path)
saver.restore(sess, ckpt_path)

out = sess.run(samples)
np.save(OUTPUT_PATH, out)
print("Saved samples to: %s" % OUTPUT_PATH)
