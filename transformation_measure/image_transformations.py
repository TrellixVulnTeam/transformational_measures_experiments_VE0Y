from  skimage import transform as skimage_transform
import numpy as np
import cv2
import itertools
from typing import List,Tuple,Iterator
from .transformation import Transformation,TransformationSet

class AffineTransformation(Transformation):
    def __init__(self,parameters):
        self.parameters=parameters
        self.transform=self.generate_transformation(parameters)

    def generate_transformation(self,transformation_parameters):
        rotation, translation, scale = transformation_parameters
        transformation = skimage_transform.AffineTransform(scale=scale, rotation=rotation, shear=None,
                                                           translation=translation)
        return transformation

    def center_transformation(self,transformation,image_size):
        shift_y, shift_x = (image_size - 1) / 2.
        shift = skimage_transform.AffineTransform(translation=[-shift_x, -shift_y])
        shift_inv = skimage_transform.AffineTransform(translation=[shift_x, shift_y])
        return shift + (transformation+ shift_inv)

    def __call__(self,image:np.ndarray)->np.ndarray:
        h,w,c=image.shape
        image_size=np.array([h, w])
        centered_transformation=self.center_transformation(self.transform,image_size)
        return skimage_transform.warp(image, centered_transformation.inverse,cval=0.0,preserve_range=True,order=1)


    def __str__(self):
        return f"Transformation {self.parameters}"

class AffineTransformationCV(Transformation):
    def __init__(self,parameters):
        self.parameters=parameters
        self.transform=self.generate_transformation(parameters)

    def __eq__(self, other):

        return self.parameters == other.parameters

    def generate_transformation(self,transformation_parameters):
        rotation, translation, scale = transformation_parameters
        transformation = skimage_transform.AffineTransform(scale=scale, rotation=rotation, shear=None,
                                                           translation=translation)
        return transformation

    def center_transformation(self,transformation,image_size):
        shift_y, shift_x = (image_size - 1) / 2.
        shift = skimage_transform.AffineTransform(translation=[-shift_x, -shift_y])
        shift_inv = skimage_transform.AffineTransform(translation=[shift_x, shift_y])
        return shift + (transformation+ shift_inv)

    def __call__(self,image:np.ndarray)->np.ndarray:
        # print(image.min(), image.max(), image.dtype, image.shape)
        image=image.transpose((1,2,0))
        h, w, c= image.shape
        # print(image.min(),image.max(),image.dtype,image.shape)
        transformation= self.center_transformation(self.transform, np.array((h, w)))
        m= transformation.params

        image= cv2.warpPerspective(image, m, (w, h))
        if c==1:
           image= image[:, :, np.newaxis]
        image = image.transpose(2,0,1)
        return image

    def inverse(self):
        rotation, translation, scale = self.parameters
        rotation=-rotation
        tx,ty=translation
        translation= (-tx,-ty)
        sx,sy=scale
        scale=(1/sx,1/sy)
        parameters = (rotation,translation,scale)
        return AffineTransformationCV(parameters)

    def __str__(self):
        return f"Transformation {self.parameters}"

TranslationParameter=Tuple[int,int]
ScaleParameter=Tuple[float,float]


class AffineTransformationGenerator(TransformationSet):
    def __init__(self,rotations:List[float]=None, scales:List[ScaleParameter]=None, translations:List[TranslationParameter]=None):
        if rotations is None or not rotations:
            rotations=[0]
        if scales is None or not scales:
            scales = [(1.0, 1.0)]
        if translations is None or not translations:
            translations = [(1, 1)]

        self.rotations:List[float]=rotations
        self.scales:List[ScaleParameter]=scales
        self.translations=translations

    def __repr__(self):
        return f"rot={self.rotations}, scales={self.scales}, translations={self.translations}"
    def id(self):
        return f"r{self.rotations}_s{self.scales}_t{self.translations}"

    def __iter__(self)->Iterator[Transformation]:
        transformation_parameters = itertools.product(self.rotations, self.translations, self.scales)
        return [AffineTransformationCV(parameter) for parameter in transformation_parameters].__iter__()


class SimpleAffineTransformationGenerator(TransformationSet):

    def __init__(self,n_rotations:int=None,n_scales:int=None,n_translations:int=None):
        if n_rotations is None:
            n_rotations = 0
        if n_scales is None:
            n_scales = 0
        if n_translations is None:
            n_translations = 0
        self.n_rotations=n_rotations
        self.n_translations=n_translations
        self.n_scales=n_scales
        rotations, translations, scales = self.generate_transformation_values()
        self.affine_transformation_generator=AffineTransformationGenerator(rotations=rotations, scales=scales, translations=translations)

    def __repr__(self):
        return f"Affine(r={self.n_rotations},s={self.n_scales},t={self.n_translations})"
    def __eq__(self, other):
        if isinstance(other,self.__class__):
            return self.n_rotations==other.n_rotations and self.n_scales==other.n_scales and self.n_translations == other.n_translations

    def id(self):
        return f"Affine(r={self.n_rotations},s={self.n_scales},t={self.n_translations})"

    def __iter__(self)->Iterator[Transformation]:
        return self.affine_transformation_generator.__iter__()


    def infinite_binary_progression(self):
        yield 1.0
        values=[ (0,1.0)]
        while True:
            new_values=[]
            for (l,u) in values:
                mid=(l+u)/2
                yield mid
                new_values.append((l,mid))
                new_values.append((mid, l))
            values=new_values
    def infinite_harmonic_series(self):
        value = 1.0
        n=1.0
        while True:
            yield value/n
            n+=1
    def infinite_geometric_series(self,base):
        n=1
        while True:
            yield pow(base,n)

    import itertools
    def generate_transformation_values(self):
        rotations = list(np.linspace(-np.pi, np.pi, self.n_rotations, endpoint=False))

        scales=[(1.0,1.0)]
        scale_series=self.infinite_geometric_series(0.5)
        for s in itertools.islice(scale_series,self.n_scales):
            r=1.0 - s
            scales.append( (r,r) )

        translations=[(0,0)]
        for t in range(self.n_translations):
            d=t+1
            translations.append( (0,d) )
            translations.append((0, -d))
            translations.append((d, 0))
            translations.append((-d, 0))
            translations.append((-d, d))
            translations.append((-d, -d))
            translations.append((d, -d))
            translations.append((d, d))

        return rotations,translations,scales