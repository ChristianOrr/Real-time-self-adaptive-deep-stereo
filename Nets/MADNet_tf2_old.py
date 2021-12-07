import tensorflow as tf
import numpy as np
import math
from Losses.loss_factory import mean_SSIM_L1

print("\nTensorFlow Version: {}".format(tf.__version__))


# dummpy data for the images
image_height = 320
image_width = 1216
input_size = (image_height, image_width)
batch_size = 1 # Set batch size to none to have a variable batch size


# ------------------------------------------------------------------------
# Model Creation
# Left and right image inputs
left_input = tf.keras.Input(shape=(image_height, image_width, 3, ), batch_size=batch_size, name="left_image_input", dtype=tf.float32)
right_input = tf.keras.Input(shape=(image_height, image_width, 3, ), batch_size=batch_size, name="right_image_input", dtype=tf.float32)

#######################PYRAMID FEATURES###############################
act = tf.keras.layers.Activation(tf.nn.leaky_relu)
# Left image feature pyramid (feature extractor)
# F1
left_pyramid = tf.keras.layers.Conv2D(filters=16, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="left_conv1")(left_input)
left_F1 = tf.keras.layers.Conv2D(filters=16, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="left_conv2")(left_pyramid)
# F2
left_pyramid = tf.keras.layers.Conv2D(filters=32, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="left_conv3")(left_F1)
left_F2 = tf.keras.layers.Conv2D(filters=32, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="left_conv4")(left_pyramid)
# F3
left_pyramid = tf.keras.layers.Conv2D(filters=64, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="left_conv5")(left_F2)
left_F3 = tf.keras.layers.Conv2D(filters=64, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="left_conv6")(left_pyramid)
# F4
left_pyramid = tf.keras.layers.Conv2D(filters=96, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="left_conv7")(left_F3)
left_F4 = tf.keras.layers.Conv2D(filters=96, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="left_conv8")(left_pyramid)
# F5
left_pyramid = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="left_conv9")(left_F4)
left_F5 = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="left_conv10")(left_pyramid)
# F6
left_pyramid = tf.keras.layers.Conv2D(filters=192, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="left_conv11")(left_F5)
left_F6 = tf.keras.layers.Conv2D(filters=192, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="left_conv12")(left_pyramid)


# Right image feature pyramid (feature extractor)
# F1
right_pyramid = tf.keras.layers.Conv2D(filters=16, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="right_conv1")(right_input)
right_F1 = tf.keras.layers.Conv2D(filters=16, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="right_conv2")(right_pyramid)
# F2
right_pyramid = tf.keras.layers.Conv2D(filters=32, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="right_conv3")(right_F1)
right_F2 = tf.keras.layers.Conv2D(filters=32, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="right_conv4")(right_pyramid)
# F3
right_pyramid = tf.keras.layers.Conv2D(filters=64, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="right_conv5")(right_F2)
right_F3 = tf.keras.layers.Conv2D(filters=64, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="right_conv6")(right_pyramid)
# F4
right_pyramid = tf.keras.layers.Conv2D(filters=96, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="right_conv7")(right_F3)
right_F4 = tf.keras.layers.Conv2D(filters=96, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="right_conv8")(right_pyramid)
# F5
right_pyramid = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="right_conv9")(right_F4)
right_F5 = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="right_conv10")(right_pyramid)
# F6
right_pyramid = tf.keras.layers.Conv2D(filters=192, kernel_size=(3,3), strides=2, padding="same", activation=act, use_bias=True, name="right_conv11")(right_F5)
right_F6 = tf.keras.layers.Conv2D(filters=192, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="right_conv12")(right_pyramid)



# https://github.com/philferriere/tfoptflow/blob/bdc7a72e78008d1cd6db46e4667dffc2bab1fe9e/tfoptflow/core_costvol.py
class StereoCostVolume(tf.keras.layers.Layer):
    """Build cost volume for associating a pixel from the left image with its corresponding pixels in the right image.
    Args:
        c1: Level of the feature pyramid of the left image
        warp: Warped level of the feature pyramid of the right image
        search_range: Search range (maximum displacement)
    """
    def __init__(self, name="cost_volume"):
        super(StereoCostVolume, self).__init__(name=name)

    def call(self, c1, warp, search_range):
        # # add loss estimating the reprojection accuracy of the pyramid level (for self supervised training/MAD)
        # reprojection_loss = mean_SSIM_L1(warp, c1)
        # self.add_loss(reprojection_loss)

        padded_lvl = tf.pad(warp, [[0, 0], [0, 0], [search_range, search_range], [0, 0]])
        width = c1.shape.as_list()[2]
        max_offset = search_range * 2 + 1

        cost_vol = []
        for i in range(0, max_offset):

            slice = padded_lvl[:, :, i:width+i, :]
            cost = tf.reduce_mean(c1 * slice, axis=3, keepdims=True)
            cost_vol.append(cost)

        cost_vol = tf.concat(cost_vol, axis=3)

        cost_curve = tf.concat([c1, cost_vol], axis=3)
        return cost_curve


# class StereoEstimator(tf.keras.layers.Layer):

#     def __init__(self, name="volume_filtering"):
#         super(StereoEstimator, self).__init__(name=name)
#         self.disp = None

#     def call(self, costs, upsampled_disp=None):
#         if upsampled_disp is not None:
#             volume = tf.keras.layers.concatenate([costs, upsampled_disp], axis=-1)
#         else:
#             volume = costs
#         # Need to check if disp was created previously,
#         # so variable doesnt get created multiple times (for autograph)
#         if self.disp is None:
#             self.disp = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp1")(volume)
#             self.disp = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp2")(self.disp)
#             self.disp = tf.keras.layers.Conv2D(filters=96, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp3")(self.disp)
#             self.disp = tf.keras.layers.Conv2D(filters=64, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp4")(self.disp)
#             self.disp = tf.keras.layers.Conv2D(filters=32, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp5")(self.disp)
#             self.disp = tf.keras.layers.Conv2D(filters=1, kernel_size=(3,3), strides=1, padding="same", activation="linear", use_bias=True, name="disp6")(self.disp)

#         return self.disp




# # https://github.com/philferriere/tfoptflow/blob/bdc7a72e78008d1cd6db46e4667dffc2bab1fe9e/tfoptflow/core_warp.py
# def dense_image_warp(image, flow, name='dense_image_warp'):
#     """Image warping using per-pixel flow vectors.
#     Apply a non-linear warp to the image, where the warp is specified by a dense
#     flow field of offset vectors that define the correspondences of pixel values
#     in the output image back to locations in the  source image. Specifically, the
#     pixel value at output[b, j, i, c] is
#     images[b, j - flow[b, j, i, 0], i - flow[b, j, i, 1], c].
#     The locations specified by this formula do not necessarily map to an int
#     index. Therefore, the pixel value is obtained by bilinear
#     interpolation of the 4 nearest pixels around
#     (b, j - flow[b, j, i, 0], i - flow[b, j, i, 1]). For locations outside
#     of the image, we use the nearest pixel values at the image boundary.
#     Args:
#       image: 4-D float `Tensor` with shape `[batch, height, width, channels]`.
#       flow: A 4-D float `Tensor` with shape `[batch, height, width, 2]`.
#       name: A name for the operation (optional).
#       Note that image and flow can be of type tf.half, tf.float32, or tf.float64,
#       and do not necessarily have to be the same type.
#     Returns:
#       A 4-D float `Tensor` with shape`[batch, height, width, channels]`
#         and same type as input image.
#     Raises:
#       ValueError: if height < 2 or width < 2 or the inputs have the wrong number
#                   of dimensions.
#     """

#     batch_size, height, width, channels = array_ops.unstack(array_ops.shape(image))
#     # The flow is defined on the image grid. Turn the flow into a list of query
#     # points in the grid space.
#     grid_x, grid_y = array_ops.meshgrid(math_ops.range(width), math_ops.range(height))
#     stacked_grid = math_ops.cast(array_ops.stack([grid_y, grid_x], axis=2), flow.dtype)
#     batched_grid = array_ops.expand_dims(stacked_grid, axis=0)
#     query_points_on_grid = batched_grid - flow
#     query_points_flattened = array_ops.reshape(query_points_on_grid, [batch_size, height * width, 2])
#     # Compute values at the query points, then reshape the result back to the
#     # image grid.
#     interpolated = _interpolate_bilinear(image, query_points_flattened)
#     interpolated = array_ops.reshape(interpolated, [batch_size, height, width, channels])
#     return interpolated

class BuildIndices(tf.keras.layers.Layer):

    def __init__(self, name="build_indices"):
        super(BuildIndices, self).__init__(name=name)

    def call(self, coords):

        batches, height, width, channels = coords.get_shape().as_list()

        pixel_coords = np.ones((1, height, width, 2), dtype=np.float32)
        batches_coords = np.ones((batches, height, width, 1), dtype=np.float32)

        for i in range(0, batches):
            batches_coords[i][:][:][:] = i
        # build pixel coordinates and their disparity
        for i in range(0, height):
            for j in range(0, width):
                pixel_coords[0][i][j][0] = j
                pixel_coords[0][i][j][1] = i

        pixel_coords = tf.constant(pixel_coords, tf.float32)
        output = tf.concat([batches_coords, pixel_coords + coords], -1)            

        return output


class Warp(tf.keras.layers.Layer):

    def __init__(self, name="warp"):
        super(Warp, self).__init__(name=name)

    def call(self, imgs, coords):
            
        coord_b, coords_x, coords_y = tf.split(coords, [1, 1, 1], axis=3)

        coords_x = tf.cast(coords_x, 'float32')
        coords_y = tf.cast(coords_y, 'float32')

        x0 = tf.floor(coords_x)
        x1 = x0 + 1
        y0 = tf.floor(coords_y)

        y_max = tf.cast(tf.shape(imgs)[1] - 1, 'float32')
        x_max = tf.cast(tf.shape(imgs)[2] - 1, 'float32')
        zero = tf.zeros([1],dtype=tf.float32)

        x0_safe = tf.clip_by_value(x0, zero[0], x_max)
        y0_safe = tf.clip_by_value(y0, zero[0], y_max)
        x1_safe = tf.clip_by_value(x1, zero[0], x_max)

        # bilinear interp weights, with points outside the grid having weight 0
        wt_x0 = (x1 - coords_x) * tf.cast(tf.equal(x0, x0_safe), 'float32')
        wt_x1 = (coords_x - x0) * tf.cast(tf.equal(x1, x1_safe), 'float32')


        im00 = tf.cast(tf.gather_nd(imgs, tf.cast(
            tf.concat([coord_b, y0_safe, x0_safe], -1), 'int32')), 'float32')
        im01 = tf.cast(tf.gather_nd(imgs, tf.cast(
            tf.concat([coord_b, y0_safe, x1_safe], -1), 'int32')), 'float32')

        output = tf.add_n([
            wt_x0 * im00, wt_x1 * im01
        ])

        return output

# class StereoContextNetwork(tf.keras.Model):

#     def __init__(self, name="residual_refinement_network"):
#         super(StereoContextNetwork, self).__init__(name=name)
#         self.context = None

#     def call(self, input, disp):

#         volume = tf.keras.layers.concatenate([input, disp], axis=-1)
#         # Need to check if context was created previously,
#         # so variable doesnt get created multiple times (for autograph)
#         if self.context is None:
#             self.context = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), dilation_rate=1, padding="same", activation=act, use_bias=True, name="context1")(volume)
#             self.context = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), dilation_rate=2, padding="same", activation=act, use_bias=True, name="context2")(self.context)
#             self.context = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), dilation_rate=4, padding="same", activation=act, use_bias=True, name="context3")(self.context)
#             self.context = tf.keras.layers.Conv2D(filters=96, kernel_size=(3,3), dilation_rate=8, padding="same", activation=act, use_bias=True, name="context4")(self.context)
#             self.context = tf.keras.layers.Conv2D(filters=64, kernel_size=(3,3), dilation_rate=16, padding="same", activation=act, use_bias=True, name="context5")(self.context)
#             self.context = tf.keras.layers.Conv2D(filters=32, kernel_size=(3,3), dilation_rate=1, padding="same", activation=act, use_bias=True, name="context6")(self.context)
#             self.context = tf.keras.layers.Conv2D(filters=1, kernel_size=(3,3), dilation_rate=1, padding="same", activation="linear", use_bias=True, name="context7")(self.context)

#         final_disp = tf.keras.layers.add([disp, self.context], name="final_disp")

#         return final_disp

class StereoContextNetwork(tf.keras.Model):

    def __init__(self, name="residual_refinement_network"):
        super(StereoContextNetwork, self).__init__(name=name)
        self.x = None
        self.context1 = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), dilation_rate=1, padding="same", activation=act, use_bias=True, name="context1")
        self.context2 = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), dilation_rate=2, padding="same", activation=act, use_bias=True, name="context2")
        self.context3 = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), dilation_rate=4, padding="same", activation=act, use_bias=True, name="context3")
        self.context4 = tf.keras.layers.Conv2D(filters=96, kernel_size=(3,3), dilation_rate=8, padding="same", activation=act, use_bias=True, name="context4")
        self.context5 = tf.keras.layers.Conv2D(filters=64, kernel_size=(3,3), dilation_rate=16, padding="same", activation=act, use_bias=True, name="context5")
        self.context6 = tf.keras.layers.Conv2D(filters=32, kernel_size=(3,3), dilation_rate=1, padding="same", activation=act, use_bias=True, name="context6")
        self.context7 = tf.keras.layers.Conv2D(filters=1, kernel_size=(3,3), dilation_rate=1, padding="same", activation="linear", use_bias=True, name="context7")

    def call(self, input, disp):

        volume = tf.keras.layers.concatenate([input, disp], axis=-1)
        # Need to check if context was created previously,
        # so variable doesnt get created multiple times (for autograph)
        if self.x is None:
            self.x = self.context1(volume)
            self.x = self.context2(self.x)
            self.x = self.context3(self.x)
            self.x = self.context4(self.x)
            self.x = self.context5(self.x)
            self.x = self.context6(self.x)
            self.x = self.context7(self.x)

        final_disp = tf.keras.layers.add([disp, self.x], name="final_disp")

        return final_disp


class StereoEstimator(tf.keras.Model):
    """
    This is the stereo estimation network at resolution n.
    It uses the costs (from the pixel difference between the warped right image 
    and the left image) combined with the upsampled disparity from the previous
    layer (when the layer is not the last layer).

    The output is predicted disparity for the network at resolution n.
    """

    def __init__(self, name="volume_filtering"):
        super(StereoEstimator, self).__init__(name=name)
        self.x = None
        self.disp1 = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp1")
        self.disp2 = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp2")
        self.disp3 = tf.keras.layers.Conv2D(filters=96, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp3")
        self.disp4 = tf.keras.layers.Conv2D(filters=64, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp4")
        self.disp5 = tf.keras.layers.Conv2D(filters=32, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp5")
        self.disp6 = tf.keras.layers.Conv2D(filters=1, kernel_size=(3,3), strides=1, padding="same", activation="linear", use_bias=True, name="disp6")

    def call(self, costs, upsampled_disp=None):
        if upsampled_disp is not None:
            volume = tf.keras.layers.concatenate([costs, upsampled_disp], axis=-1)
        else:
            volume = costs
        # Need to check if disp was created previously,
        # so variable doesnt get created multiple times (for autograph)
        if self.x is None:
            x = self.disp1(volume)
            x = self.disp2(x)
            x = self.disp3(x)
            x = self.disp4(x)
            x = self.disp5(x)
            x = self.disp6(x)
        return x


class ModuleM(tf.keras.Model):
    """
    Module MX is a sub-module of MADNet, which can be trained individually for 
    online adaptation using the MAD (Modular ADaptaion) method.
    """
    def __init__(self, name="MX", layer="X", search_range=2):
        super(ModuleM, self).__init__(name=name)
        self.module_disparity = None
        self.final_disparity = None
        self.context_disparity = None
        self.search_range = search_range
        self.layer = layer
        self.cost_volume = StereoCostVolume(name=f"cost_{layer}")
        self.stereo_estimator = StereoEstimator(name=f"volume_filtering_{layer}")
        self.context_network = StereoContextNetwork()

    def call(self, left, right, prev_disp=None, is_final_module=False):

        height, width = (left.shape.as_list()[1], left.shape.as_list()[2])
        # Check if module disparity was previously calculated to prevent retracing (for autograph)
        if self.module_disparity is not None:
            # Check if layer is the bottom of the pyramid
            if prev_disp is not None:
                # Upsample disparity from previous layer
                upsampled_disp = tf.keras.layers.Resizing(name=f"upsampled_disp_{self.layer}", height=height, width=width, interpolation='bilinear')(prev_disp)
                coords = tf.keras.layers.concatenate([upsampled_disp, tf.zeros_like(upsampled_disp)], -1)
                indices = BuildIndices(name=f"build_indices_{self.layer}")(coords)
                # Warp the right image into the left using upsampled disparity
                warped_left = Warp(name=f"warp_{self.layer}")(right, indices)
            else:
                # No previous disparity exits, so use right image instead of warped left
                warped_left = right

            # add loss estimating the reprojection accuracy of the pyramid level (for self supervised training/MAD)
            reprojection_loss = mean_SSIM_L1(warped_left, left)
            self.add_loss(reprojection_loss)

            costs = self.cost_volume(left, warped_left, self.search_range)
            # Get the disparity using cost volume between left and warped left images
            self.module_disparity = self.stereo_estimator(costs)

        # Add the residual refinement network to the final layer
        # also check if disparity was created previously (for autograph)
        if is_final_module and self.final_disparity is not None:
            self.context_disparity = self.context_network(left, self.module_disparity)
            self.final_disparity = tf.keras.layers.Resizing(name="final_disparity", height=height, width=width, interpolation='bilinear')(self.context_disparity)


        return self.final_disparity if is_final_module else self.module_disparity





search_range = 2 # maximum dispacement

#############################SCALE 6#################################
M6 = ModuleM(name="M6", layer="6", search_range=search_range)(left_F6, right_F6)

############################SCALE 5###################################
M5 = ModuleM(name="M5", layer="5", search_range=search_range)(left_F5, right_F5, M6)

############################SCALE 4###################################
M4 = ModuleM(name="M4", layer="4", search_range=search_range)(left_F4, right_F4, M5)

############################SCALE 3###################################
M3 = ModuleM(name="M3", layer="3", search_range=search_range)(left_F3, right_F3, M4)

############################SCALE 2###################################
M2 = ModuleM(name="M2", layer="2", search_range=search_range)(left_F2, right_F2, M3, True)



MADNet = tf.keras.Model(inputs=[left_input, right_input], outputs=M2, name="MADNet")


MADNet.compile(
    optimizer='adam'
)

MADNet.summary()
#tf.keras.utils.plot_model(MADNet, "./images/MADNet Model Structure.png", show_layer_names=True)


# --------------------------------------------------------------------------------
# Data Preperation

left_dir = "G:/My Drive/Data Files/2011_09_26_drive_0002_sync/left"
right_dir = "G:/My Drive/Data Files/2011_09_26_drive_0002_sync/right"

# Create datagenerator object for loading and preparing image data for training
left_dataflow_kwargs = dict(
    directory = left_dir, 
    target_size = input_size, 
    class_mode = None,
    batch_size = batch_size,
    shuffle = False,     
    interpolation = "bilinear",
    )

right_dataflow_kwargs = dict(
    directory = right_dir, 
    target_size = input_size, 
    class_mode = None,
    batch_size = batch_size,
    shuffle = False,     
    interpolation = "bilinear",
    )


# Normalize pixel values
datagen_args = dict(
    rescale = 1./255
        )

datagen = tf.keras.preprocessing.image.ImageDataGenerator(**datagen_args)

left_generator = datagen.flow_from_directory(**left_dataflow_kwargs)
right_generator = datagen.flow_from_directory(**right_dataflow_kwargs)

def generator(left_generator, right_generator):
    """Combines the left and right image generators into a 
        single image generator with two inputs for training.
        
        Make sure the left and right images have the same ID,
        otherwise the order might change which will pair the wrong
        left and right images."""
    while True:
        left = left_generator.next()
        right = right_generator.next()
        yield [left, right], None

steps_per_epoch = math.ceil(left_generator.samples / batch_size)


# ---------------------------------------------------------------------------
# Train the model

history = MADNet.fit(
    x=generator(left_generator, right_generator),
    batch_size=batch_size,
    epochs=1,
    verbose=2,
    steps_per_epoch=steps_per_epoch
)




# # Stereo estimator model
# def _stereo_estimator(num_filters=1, model_name="fgc-volume-filtering"):
#     volume = tf.keras.Input(shape=(None, None, num_filters, ), name="cost_volume", dtype=tf.float32)

#     disp = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp1")(volume)
#     disp = tf.keras.layers.Conv2D(filters=128, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp2")(disp)
#     disp = tf.keras.layers.Conv2D(filters=96, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp3")(disp)
#     disp = tf.keras.layers.Conv2D(filters=64, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp4")(disp)
#     disp = tf.keras.layers.Conv2D(filters=32, kernel_size=(3,3), strides=1, padding="same", activation=act, use_bias=True, name="disp5")(disp)
#     disp = tf.keras.layers.Conv2D(filters=1, kernel_size=(3,3), strides=1, padding="same", activation=None, use_bias=True, name="disp6")(disp)

#     return tf.keras.Model(inputs=[volume], outputs=[disp], name=model_name)
