import os
import numpy as np
import tensorflow as tf
from PIL import Image
import json
import sys

# Import the preprocessing function
from .preprocessing import create_preprocessing_fn

class TFLitePlantDiseaseInferencePipeline:
    """TFLite-based multi-stage inference pipeline for plant disease detection."""
    
    def __init__(self, config_path=None, plant_model_path=None, coffee_model_path=None, 
                 banana_model_path=None, plant_threshold=0.7, disease_threshold=0.5,
                 plant_classes=None, coffee_disease_classes=None, banana_disease_classes=None):
        """Initialize the TFLite inference pipeline."""
        
        # Load from config if provided
        if config_path:
            with open(config_path, 'r') as f:
                config = json.load(f)
                plant_model_path = config.get('plant_model_path', plant_model_path)
                coffee_model_path = config.get('coffee_model_path', coffee_model_path)
                banana_model_path = config.get('banana_model_path', banana_model_path)
                plant_classes = config.get('plant_classes', plant_classes)
                coffee_disease_classes = config.get('coffee_disease_classes', coffee_disease_classes)
                banana_disease_classes = config.get('banana_disease_classes', banana_disease_classes)
        
        self.plant_threshold = plant_threshold
        self.disease_threshold = disease_threshold
        
        # Load TFLite models
        print("Loading plant classifier model...")
        self.plant_interpreter = tf.lite.Interpreter(model_path=plant_model_path)
        self.plant_interpreter.allocate_tensors()
        
        print("Loading coffee disease model...")
        self.coffee_interpreter = tf.lite.Interpreter(model_path=coffee_model_path)
        self.coffee_interpreter.allocate_tensors()
        
        print("Loading banana disease model...")
        self.banana_interpreter = tf.lite.Interpreter(model_path=banana_model_path)
        self.banana_interpreter.allocate_tensors()
        
        # Get input/output details
        self.plant_input_details = self.plant_interpreter.get_input_details()
        self.plant_output_details = self.plant_interpreter.get_output_details()
        
        self.coffee_input_details = self.coffee_interpreter.get_input_details()
        self.coffee_output_details = self.coffee_interpreter.get_output_details()
        
        self.banana_input_details = self.banana_interpreter.get_input_details()
        self.banana_output_details = self.banana_interpreter.get_output_details()
        
        # Store class names
        self.plant_classes = plant_classes or ['coffee', 'banana', 'other']
        self.coffee_disease_classes = coffee_disease_classes or ['healthy', 'leaf_rust', 'coffee_berry_disease', 'red_spider_mite']
        self.banana_disease_classes = banana_disease_classes or ['healthy', 'black_sigatoka', 'yellow_sigatoka', 'panama_disease']
        
        # Create preprocessing functions using the original implementation
        self.plant_preprocess_fn = create_preprocessing_fn(
            model_type='plant', 
            normalization_type='efficientnet'
        )
        
        self.coffee_preprocess_fn = create_preprocessing_fn(
            model_type='coffee', 
            normalization_type='efficientnet', 
            use_segmentation=True
        )
        
        self.banana_preprocess_fn = create_preprocessing_fn(
            model_type='banana', 
            normalization_type='efficientnet', 
            use_segmentation=True
        )
    
    def _process_for_interpreter(self, img_tensor):
        """Convert TensorFlow tensor to numpy array for interpreter."""
        if isinstance(img_tensor, tf.Tensor):
            return img_tensor.numpy()
        return img_tensor
    
    def predict(self, image_path):
        """Make a prediction using the TFLite multi-stage pipeline."""
        # Stage 1: Plant Classification
        plant_img = self.plant_preprocess_fn(image_path)
        plant_img_np = self._process_for_interpreter(plant_img)
        plant_img_np = np.expand_dims(plant_img_np, axis=0).astype(np.float32)
        
        # Set input tensor and invoke
        self.plant_interpreter.set_tensor(self.plant_input_details[0]['index'], plant_img_np)
        self.plant_interpreter.invoke()
        
        # Get output tensor
        plant_preds = self.plant_interpreter.get_tensor(self.plant_output_details[0]['index'])[0]
        
        plant_class_idx = np.argmax(plant_preds)
        plant_confidence = plant_preds[plant_class_idx]
        
        # Check if confidence is above threshold
        if plant_confidence < self.plant_threshold:
            return {
                "plant_type": "unknown",
                "plant_confidence": float(plant_confidence),
                "disease_status": "unknown",
                "disease_confidence": 0.0,
                "all_plant_probabilities": {
                    class_name: float(prob) for class_name, prob in zip(self.plant_classes, plant_preds)
                }
            }
        
        # Get plant type
        plant_type = self.plant_classes[plant_class_idx]
        
        # Stage 2: Disease Detection based on plant type
        if plant_type == "coffee":
            preprocess_fn = self.coffee_preprocess_fn
            interpreter = self.coffee_interpreter
            input_details = self.coffee_input_details
            output_details = self.coffee_output_details
            disease_classes = self.coffee_disease_classes
        elif plant_type == "banana":
            preprocess_fn = self.banana_preprocess_fn
            interpreter = self.banana_interpreter
            input_details = self.banana_input_details
            output_details = self.banana_output_details
            disease_classes = self.banana_disease_classes
        else:
            # For other plant types, we don't have a specific disease model
            return {
                "plant_type": plant_type,
                "plant_confidence": float(plant_confidence),
                "disease_status": "unknown",
                "disease_confidence": 0.0,
                "all_plant_probabilities": {
                    class_name: float(prob) for class_name, prob in zip(self.plant_classes, plant_preds)
                }
            }
        
        # Make disease prediction using the right preprocessing
        disease_img = preprocess_fn(image_path)
        disease_img_np = self._process_for_interpreter(disease_img)
        disease_img_np = np.expand_dims(disease_img_np, axis=0).astype(np.float32)
        
        # Set input tensor and invoke
        interpreter.set_tensor(input_details[0]['index'], disease_img_np)
        interpreter.invoke()
        
        # Get output tensor
        disease_preds = interpreter.get_tensor(output_details[0]['index'])[0]
        
        disease_class_idx = np.argmax(disease_preds)
        disease_confidence = disease_preds[disease_class_idx]
        
        # Check if confidence is above threshold
        if disease_confidence < self.disease_threshold:
            disease_status = "unknown"
        else:
            disease_status = disease_classes[disease_class_idx]
        
        # Return result
        return {
            "plant_type": plant_type,
            "plant_confidence": float(plant_confidence),
            "disease_status": disease_status,
            "disease_confidence": float(disease_confidence),
            "all_plant_probabilities": {
                class_name: float(prob) for class_name, prob in zip(self.plant_classes, plant_preds)
            },
            "all_disease_probabilities": {
                class_name: float(prob) for class_name, prob in zip(disease_classes, disease_preds)
            }
        }
    
    def test_time_augmentation(self, image_path, num_augmentations=5):
        """Apply test-time augmentation for more robust predictions."""
        # First get the basic prediction
        base_result = self.predict(image_path)
        
        # If plant confidence is below threshold, return basic result
        if base_result["plant_type"] == "unknown":
            return base_result
            
        # Determine which model to use for disease prediction
        plant_type = base_result["plant_type"]
        
        # Only apply TTA for coffee or banana
        if plant_type not in ["coffee", "banana"]:
            return base_result
            
        # Select appropriate preprocessing and model
        if plant_type == "coffee":
            preprocess_fn = self.coffee_preprocess_fn
            interpreter = self.coffee_interpreter
            input_details = self.coffee_input_details
            output_details = self.coffee_output_details
            disease_classes = self.coffee_disease_classes
        else:  # banana
            preprocess_fn = self.banana_preprocess_fn
            interpreter = self.banana_interpreter
            input_details = self.banana_input_details
            output_details = self.banana_output_details
            disease_classes = self.banana_disease_classes
            
        # Collect all predictions
        all_preds = []
        
        # Base prediction (already done, just get the disease probabilities)
        base_disease_probs = base_result["all_disease_probabilities"]
        base_probs_array = np.array([base_disease_probs[cls] for cls in disease_classes])
        all_preds.append(base_probs_array)
        
        # Create augmentations
        for i in range(num_augmentations):
            # Create augmented file path by adding transformations
            augmented_path = f"{os.path.splitext(image_path)[0]}_aug_{i}{os.path.splitext(image_path)[1]}"
            
            # Load and augment the image using PIL
            img = Image.open(image_path).convert('RGB')
            
            # Apply basic augmentations
            if i % 2 == 0:  # Flip horizontally for half of augmentations
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            
            if i % 3 == 0:  # Slight rotation for some augmentations
                img = img.rotate(10 if i % 2 == 0 else -10, resample=Image.BICUBIC, expand=False)
                
            # Save augmented image temporarily
            img.save(augmented_path)
            
            try:
                # Process the augmented image
                aug_img = preprocess_fn(augmented_path)
                aug_img_np = self._process_for_interpreter(aug_img)
                aug_img_np = np.expand_dims(aug_img_np, axis=0).astype(np.float32)
                
                # Run prediction
                interpreter.set_tensor(input_details[0]['index'], aug_img_np)
                interpreter.invoke()
                aug_preds = interpreter.get_tensor(output_details[0]['index'])[0]
                all_preds.append(aug_preds)
            except Exception as e:
                print(f"Error during augmentation {i}: {e}")
            finally:
                # Remove temporary file
                try:
                    os.remove(augmented_path)
                except:
                    pass
        
        # Average predictions
        avg_preds = np.mean(all_preds, axis=0)
        disease_class_idx = np.argmax(avg_preds)
        disease_confidence = avg_preds[disease_class_idx]
        
        # Check if confidence is above threshold
        if disease_confidence < self.disease_threshold:
            disease_status = "unknown"
        else:
            disease_status = disease_classes[disease_class_idx]
            
        # Update result
        result = base_result.copy()
        result["disease_status"] = disease_status
        result["disease_confidence"] = float(disease_confidence)
        result["all_disease_probabilities"] = {
            class_name: float(prob) for class_name, prob in zip(disease_classes, avg_preds)
        }
        
        return result