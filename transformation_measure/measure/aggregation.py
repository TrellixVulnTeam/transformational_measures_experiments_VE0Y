import scipy.spatial.distance
import numpy as np
# import ray
#
# import multiprocessing
# pool = multiprocessing.Pool(4)
# from joblib import Parallel,delayed
#
# parallel = Parallel(n_jobs=2,max_nbytes=1e32)

class DistanceAggregation:

    def __init__(self,normalize:bool,keep_feature_maps:bool,distance="euclidean"):
        self.normalize=normalize
        self.keep_feature_maps=keep_feature_maps
        self.distance=distance


    @property
    def name(self):
        return f"DA(normalize={self.normalize},keep_feature_maps={self.keep_feature_maps},distance={self.distance}" # TODO add parenthesis at the end

    def apply(self,x:np.ndarray):
        x = self.convert_to_cnd_format(x)
        # x has size (c,n,d), where c is the feature dimension
        if self.normalize:
            x -= x.min(axis=0, keepdims=True)
            max_values=x.max(axis=0,keepdims=True)
            max_values[max_values==0]=1
            x/=max_values
        return self.aggregate_distances(x)

    def convert_to_cnd_format(self,x:np.ndarray):
        l = len(x.shape)
        # Convert x to shape (n, features, dim_features)
        if l == 4:
            n, c, h, w = x.shape
            if self.keep_feature_maps:
                # consider feature maps as a whole object of size h*w
                x = x.reshape((n, c, h * w))
            else:
                # consider every element of the feature map as a distinct activation
                x = x.reshape((n, c * h * w, 1))
        elif l == 2:
            n,c=x.shape
            x = x.reshape((n, c, 1))
        else:
            raise ValueError(f"Activation shape not supported {x.shape}")
        # ncd to cnd
        x = x.transpose((1, 0, 2))
        #print(x.flags["C_CONTIGUOUS"])
        x = np.ascontiguousarray(x)
        return x

    def aggregate_distances(self, x: np.ndarray):
        c,n, d = x.shape
        results = np.zeros(c)
        for i in range(c):
            sample = x[i, :,:]
            dm = scipy.spatial.distance.pdist(sample, self.distance)
            results[i]= dm.mean()
        return results

