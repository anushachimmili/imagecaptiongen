import os
import pickle
from transformers import BlipProcessor, BlipForConditionalGeneration,AutoProcessor, AutoModelForCausalLM

# Blip Model Initialization
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")


# Save Blip models as pickle files
with open(os.path.join('ml_models','blip_processor.pkl'), 'wb') as blip_processor_file:
    pickle.dump(blip_processor, blip_processor_file)

with open(os.path.join('ml_models','blip_model.pkl'), 'wb') as blip_model_file:
    pickle.dump(blip_model, blip_model_file)


# Microsoft Git-Base-COCO Model Initialization
git_processor = AutoProcessor.from_pretrained("microsoft/git-base-coco")
git_model = AutoModelForCausalLM.from_pretrained("microsoft/git-base-coco")


# Save Microsoft Git-Base-COCO models as pickle files
with open(os.path.join('ml_models','git_processor.pkl'), 'wb') as git_processor_file:
    pickle.dump(git_processor, git_processor_file)

with open(os.path.join('ml_models','git_model.pkl'), 'wb') as git_model_file:
    pickle.dump(git_model, git_model_file)
