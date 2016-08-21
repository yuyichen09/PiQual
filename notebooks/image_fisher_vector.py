import numpy as np
import h5py
import os
import cv2
from sklearn.decomposition import PCA
import ggmm.gpu as ggmm

from sklearn import svm
from sklearn.metrics import accuracy_score


import pandas as pd
from pandas import HDFStore, DataFrame
#import pdb

class ImageFisherVector(object):
    dataset_dir = '../dataset_h5/'
    skipped_indices = []
    filename = 'images_224_delta_1.5.h5'
    test_filename = 'images.h5'
    def __init__(self):
        h5f = h5py.File(os.path.join(dataset_dir,filename),'r')
        try:
            skipped_indices = np.load("skipped_indices.npy")
            fv = np.load("fisher_vector.npy")
        except FileNotFoundError:
            skipped_indices, fv = process_images(h5f['data'])
            np.save("skipped_indices.npy",skipped_indices )
            np.save("fisher_vector.npy",fv )
            
        labels = load_labels(skipped_indices, 'labels_train')
        classifier = train(fv,labels)


        h5f_test = h5py.File(os.path.join(dataset_dir,test_filename),'r')
        X_test = h5f_test['data_test'][:]
        skipped_indices_test, fv_test = process_images(X_test)

        labels_test = load_labels(skipped_indices_test, 'labels_test')

        accuracy_score(labels_test, classifier.predict(fv_test))


    def process_images(images):
        skipped_indices = []
        image_features_list = []
        print("Running SIFT on Images ...")
        for index, image in enumerate(images):
            image_features = extract_image_features(image,index, skipped_indices)
            if image_features is not None:
                image_features_list.append(image_features)

        image_descriptors_reduced = reduce_features(image_features_list)

        print("Generating GMM")
        gmm = generate_gmm(image_descriptors_reduced)

        print("Generating Fisher Vector")
        fv = [ fisher_vector(image,gmm) for image in image_descriptors_reduced]

        return skipped_indices, fv



        #return (skipped_indices, np.asarray(image_features_list))

        #return [extract_image_features(image,index, skipped_indices) for index, image in enumerate(images, 1)]

    def load_labels(images_with_no_features, label_type, n_labels=-1):
        store = HDFStore('../dataset_h5/labels.h5')
        ava_table = store[label_type]
        if(label_type == 'labels_train'):
            ava_table = ava_table[( abs(ava_table.score - 5) >= 1.5)]

        #if n_labels < images_with_no_features[len(images_with_no_features) - 1]:
        #    images_with_no_features = [i for i in images_with_no_features if i <= n_labels]
        if(n_labels!=-1):
            ava_table = ava_table.head(n_labels)
        ava_table = ava_table.drop(ava_table.iloc[images_with_no_features].index.values)

        return ava_table.good



    def extract_image_features(image, current_index,skipped_indices):
        sift = cv2.xfeatures2d.SIFT_create()
        image_bgr = cv2.cvtColor(image.T, cv2.COLOR_RGB2BGR)
        _ , descriptors =  sift.detectAndCompute(image_bgr, None)
        try:
            descriptors.shape
        except AttributeError:
            print(current_index)
            skipped_indices.append(current_index)
        return descriptors



    def reduce_features(image_descriptors):
        pca = PCA(n_components=64)# adjust yourself
        pca.fit(np.concatenate(image_descriptors[:5000]))
        return np.asarray([ pca.transform(image) for image in image_descriptors])

    def generate_gmm(image_descriptors_reduced):
        concatenated_descriptors = np.concatenate(image_descriptors_reduced)
        N, D = concatenated_descriptors.shape
        K=128

        ggmm.init(3712925)
        gmm = ggmm.GMM(K,D)

        thresh = 1e-3 # convergence threshold
        n_iter = 500 # maximum number of EM iterations
        init_params = 'wmc' # initialize weights, means, and covariances

        # train GMM
        gmm.fit(concatenated_descriptors, thresh, n_iter, init_params=init_params)

        return gmm


    def fisher_vector(xx, gmm):
        """Computes the Fisher vector on a set of descriptors.
        Parameters
        ----------
        xx: array_like, shape (N, D) or (D, )
            The set of descriptors
        gmm: instance of sklearn mixture.GMM object
            Gauassian mixture model of the descriptors.
        Returns
        -------
        fv: array_like, shape (K + 2 * D * K, )
            Fisher vector (derivatives with respect to the mixing weights, means
            and variances) of the given descriptors.
        Reference
        ---------
        J. Krapac, J. Verbeek, F. Jurie.  Modeling Spatial Layout with Fisher
        Vectors for Image Categorization.  In ICCV, 2011.
        http://hal.inria.fr/docs/00/61/94/03/PDF/final.r1.pdf
        """
        xx = np.atleast_2d(xx)
        N = xx.shape[0]

        # Compute posterior probabilities.
        Q = gmm.compute_posteriors(xx)  # NxK
        
        Q = Q.asarray()

        # Compute the sufficient statistics of descriptors.
        Q_sum = np.sum(Q, 0)[:, np.newaxis] / N
        Q_xx = np.dot(Q.T, xx) / N
        Q_xx_2 = np.dot(Q.T, xx ** 2) / N

        # Compute derivatives with respect to mixing weights, means and variances.
        d_pi = Q_sum.squeeze() - gmm.get_weights()
        d_mu = Q_xx - Q_sum * gmm.get_means()
        d_sigma = (
            - Q_xx_2
            - Q_sum * gmm.get_means() ** 2
            + Q_sum * gmm.get_covars()
            + 2 * Q_xx * gmm.get_means())

        # Merge derivatives into a vector.
        return np.hstack((d_pi, d_mu.flatten(), d_sigma.flatten()))

    def train(features, labels):
        X = features
        Y = labels

        clf = svm.LinearSVC()
        clf.fit(X, Y)

        return clf