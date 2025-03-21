"""Image preprocessing functions for the plant disease detection system."""

import tensorflow as tf
from .config import IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS

def load_and_resize_image(file_path, target_size=(IMG_HEIGHT, IMG_WIDTH)):
    """
    Load an image from file and resize it.
    
    Args:
        file_path: Path to the image file
        target_size: Tuple of (height, width) for resizing
    
    Returns:
        img: Preprocessed image tensor
    """
    # Read the file
    img = tf.io.read_file(file_path)
    
    # Decode the image
    # Use decode_png or decode_jpeg based on file extension
    file_path_lower = tf.strings.lower(file_path)
    
    is_png = tf.strings.regex_full_match(file_path_lower, '.*\.png')
    is_jpeg = tf.strings.regex_full_match(file_path_lower, '.*\.(jpg|jpeg)')
    
    def decode_png():
        return tf.image.decode_png(img, channels=IMG_CHANNELS)
    
    def decode_jpeg():
        return tf.image.decode_jpeg(img, channels=IMG_CHANNELS)
    
    # Default to JPEG if not PNG or JPEG (will likely fail but provides a fallback)
    def decode_default():
        return tf.image.decode_jpeg(img, channels=IMG_CHANNELS)
    
    # Conditional decoding based on file type
    img = tf.case([
        (is_png, decode_png),
        (is_jpeg, decode_jpeg)
    ], default=decode_default)
    
    # Resize the image
    img = tf.image.resize(img, target_size)
    
    return img

def normalize_image(img, normalization_type='efficientnet'):
    """
    Normalize image values based on the specified model's requirements.
    
    Args:
        img: Image tensor
        normalization_type: Type of normalization to apply
    
    Returns:
        normalized_img: Normalized image tensor
    """
    if normalization_type == 'efficientnet':
        # EfficientNet preprocessing
        return tf.keras.applications.efficientnet.preprocess_input(img)
    elif normalization_type == 'resnet':
        # ResNet preprocessing
        return tf.keras.applications.resnet_v2.preprocess_input(img)
    elif normalization_type == 'standard':
        # Standard normalization to [0, 1]
        return img / 255.0
    else:
        raise ValueError(f"Unknown normalization type: {normalization_type}")

def preprocess_plant_image(file_path, normalization_type='efficientnet'):
    """
    Preprocess an image for the plant classifier model.
    
    Args:
        file_path: Path to the image file
        normalization_type: Type of normalization to apply
    
    Returns:
        img: Preprocessed image tensor
    """
    img = load_and_resize_image(file_path)
    img = normalize_image(img, normalization_type)
    return img

def leaf_segmentation(img, threshold=0.7):
    """
    Simple leaf segmentation to focus on the leaf area.
    Uses green channel prominence as a heuristic.
    
    Args:
        img: Image tensor (0-255 value range)
        threshold: Threshold for green ratio
    
    Returns:
        masked_img: Image with background masked out
    """
    # Convert to float32 if not already
    img = tf.cast(img, tf.float32)
    
    # Calculate green ratio (G / (R+G+B))
    r, g, b = tf.unstack(img, axis=-1)
    rgb_sum = r + g + b
    # Avoid division by zero
    rgb_sum = tf.maximum(rgb_sum, 1e-6)
    green_ratio = g / rgb_sum
    
    # Create a mask where green ratio is above threshold
    mask = tf.cast(green_ratio > threshold, tf.float32)
    
    # Apply mask to image
    masked_img = img * tf.expand_dims(mask, -1)
    
    return masked_img

def create_preprocessing_fn(model_type='plant', normalization_type='efficientnet', use_segmentation=False):
    """
    Create a preprocessing function for a specific model.
    
    Args:
        model_type: Type of model ('plant', 'coffee', 'banana')
        normalization_type: Type of normalization to apply
        use_segmentation: Whether to apply leaf segmentation
    
    Returns:
        preprocessing_fn: Function that preprocesses an image file path
    """
    def preprocessing_fn(file_path):
        # Load and resize image
        img = load_and_resize_image(file_path)
        
        # Apply leaf segmentation if requested
        if use_segmentation:
            # Segmentation works on raw image values
            img_raw = img
            img = leaf_segmentation(img_raw)
        
        # Apply normalization
        img = normalize_image(img, normalization_type)
        
        return img
    
    return preprocessing_fn