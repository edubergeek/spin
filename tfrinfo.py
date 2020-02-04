import tensorflow as tf
import numpy as np


pathTrain = './data/trn-patch.tfr'  # The TFRecord file containing the training set
pathValid = './data/val-patch.tfr'    # The TFRecord file containing the validation set
pathTest = './data/tst-patch.tfr'    # The TFRecord file containing the test set

batchSize=32
batchN=300
nTrain=0
nValid=0
nTest=0

with tf.device('/cpu:0'):
  with tf.Session() as sess:
    feature = {
        'magfld': tf.FixedLenSequenceFeature(shape=[], dtype=tf.float32, allow_missing=True),
        'stokes': tf.FixedLenSequenceFeature(shape=[], dtype=tf.float32, allow_missing=True),
        'name':   tf.FixedLenFeature(shape=[], dtype=tf.string)
      }
        
    # Create a list of filenames and pass it to a queue
    filename_queue = tf.train.string_input_producer([pathTrain], num_epochs=1)
    # Define a reader and read the next record
    reader = tf.TFRecordReader()
    _, serialized_example = reader.read(filename_queue)
    # Decode the record read by the reader
    features = tf.parse_single_example(serialized_example, features=feature)
  
    name = features['name']
    # Any preprocessing here ...
    
    # Creates batches by randomly shuffling tensors
    Name = tf.train.batch([name], batch_size=batchSize)
  
    # Initialize all global and local variables
    init_op = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
    sess.run(init_op)
    # Create a coordinator and run all QueueRunner objects
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(coord=coord)
  
    # Now we read batches of images and labels and plot them
    if True:
      print("nTrain", end =" ")
      for batch_index in range(batchN):
          try:
              fname = sess.run([Name])
          except tf.errors.OutOfRangeError:
              print("End of dataset")  # "End of dataset"
              nTrain += fname[0].size
              break
          print(fname)
          nTrain += fname[0].size
          if batch_index % 10 == 0:
              print("%d"%(nTrain), end =" ")
      print("")
  
    if False:
      print("nValid", end =" ")
      filename_queue = tf.train.string_input_producer([pathValid], num_epochs=1)
      sess.run(init_op)
      # Now we read batches of images and labels and plot them
      for batch_index in range(batchN):
          try:
              fname = sess.run([Name])
          except tf.errors.OutOfRangeError:
              print("End of dataset")  # "End of dataset"
              nValid += fname[0].size
              break
          print(fname)
          nValid += fname[0].size
          if batch_index % 10 == 0:
              print("%d"%(nValid), end =" ")
      print("")
    
    if False:
      print("nTest", end =" ")
      filename_queue = tf.train.string_input_producer([pathTest], num_epochs=1)
      sess.run(init_op)
      # Now we read batches of images and labels and plot them
      for batch_index in range(batchN):
          try:
              fname = sess.run([Name])
          except tf.errors.OutOfRangeError:
              print("End of dataset")  # "End of dataset"
              break
          print(fname)
          nTest += fname[0].size
          if batch_index % 10 == 0:
              print("%d"%(nTest), end =" ")
      print("")
    
    # Stop the threads
    coord.request_stop()
    
    # Wait for threads to stop
    coord.join(threads)
    sess.close()
    print('%d training examples'%(nTrain))
    print('%d training examples'%(nValid))
    print('%d training examples'%(nTest))
