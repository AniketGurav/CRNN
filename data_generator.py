import cv2
import numpy as np 
import linecache
import abc

import keras

class Generator(keras.utils.Sequence):

	__metaclass__  = abc.ABCMeta

	def __init__(self, batch_size, img_size, nb_channels, label_len, shuffle=True):		
		self.batch_size = batch_size
		self.img_size = img_size
		self.nb_channels = nb_channels
		self.label_len = label_len
		self.timesteps = timesteps
		self.shuffle = shuffle
		self.nb_samples = len(self.filenames)
		self.on_epoch_end()

	def __len__(self):
		'''Denotes the number of batches per epoch'''
        return int(np.floor(self.nb_samples / self.batch_size))

	def __getitem__(self):
        '''Generates one batch of data'''
        indices = self.indices[index*self.batch_size:(index+1)*self.batch_size]

        batch_filenames = [self.filenames[i] for i in indices]

        X, y = self.__generate_data(batch_filenames)

	def on_epoch_end(self):
		self.indices = np.arange(self.nb_samples)
		if self.shuffle:
			np.random.shuffle(self.indices)

	def load_image(self, img_path):
		if self.nb_channels == 1:
			return cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
		else:
			return cv2.imread(img_path)

    def load_image_and_annotation(self, fn):
    	img = []
    	word = []
    	while True:
			fn_split = fn.split()
			word = linecache.getline(os.path.join(self.base_dir, self.lexicon_path), int(fn_split[1]) + 1).strip('\n')
			img_path = os.path.join(self.base_dir, fn_split[0][1:])
			img = self.load_image(img_path)

			if (img is not None) and len(word) <= self.label_len:
				loaded_img_shape = img.shape
				if img_size[0] > 2 and img_size[1] > 2:
					break

			if loaded_img_shape[1] / loaded_img_shape[0].astype('float') < 6.4:
				img = self.pad_image(img, loaded_img_shape)
			else:
				img = self.resize_image(img)

		return img, word

	def pad_image(self, img, loaded_img_shape):
		# img_size : (width, height)
		# loaded_img_shape : (height, width)
	    img_reshape = cv2.resize(img, (int(self.img_size[1] / loaded_img_shape[0] * loaded_img_shape[1]), self.img_size[1]))
	    if self.nb_channels == 1:
	        padding = np.zeros((self.img_size[1], self.img_size[0] - int(self.img_size[1] / loaded_img_shape[0] * loaded_img_shape[1])), dtype=np.int32)
	    else:
	        padding = np.zeros((self.img_size[1], self.img_size[0] - int(self.img_size[1] / loaded_img_shape[0] * loaded_img_shape[1]), self.nb_channels), dtype=np.int32)
	    img = np.concatenate([img_reshape, padding], axis=1)
	    return img

	def resize_image(img):
	    img = cv2.resize(img, self.img_size, interpolation=cv2.INTER_CUBIC)
	    img = np.asarray(img)
	    return img

	def preprocess(self, img):
	    if self.nb_channels == 1:
	        img = img.transpose([1, 0])
	    else:
	        img = img.transpose([1, 0, 2])
	    img = np.flip(img, 1)
	    img = img / 255.0
	    if self.nb_channels == 1:
	        img = img[:, :, np.newaxis]
	    return img


    @abc.abstract_method
	def __generate_data(self, batch_filenames):
		'''Method to generate batches of data'''


class TrainGenerator(Generator):

	def __generate_data(self, batch_filenames):		
		x = np.zeros((self.batch_size, *self.img_size, self.nb_channels))
		y = np.zeros((self.batch_size, self.label_len), dtype=np.uint8)

		for i, fn in enumerate(batch_filenames):
			img, word = self.load_image_and_annotation(fn)

			img = self.preprocess_image(img)
			x[i] = img

			while len(word) < self.label_len:
				word += '-'
			y[i] = [self.characters.find(c) for c in word]

		yield [x, y, np.ones(self.batch_size) * int(self.timesteps - 2), np.ones(self.batch_size) * self.label_len], y



class ValGenerator(Generator):

	def __generate_data(self, batch_filenames):
		x = np.zeros((self.batch_size, *self.img_size, self.nb_channels))
		y = []

		for i, fn in enumerate(batch_filenames):
			img, word = self.load_image_and_annotation(fn)

			img = self.preprocess_image(img)
			x[i] = img

			y.append(word)

		yield x, y