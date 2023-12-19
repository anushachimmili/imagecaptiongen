import os
import re
import io
import base64
import pickle
import requests
import secrets
from PIL import Image
from flask import flash, current_app
from imagecaptiongen.models import ImgCap
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from flask_login import current_user
from imagecaptiongen import db  


def check_prediction_limit(user, images):
    user_predictions = ImgCap.query.filter_by(author=user).count()
    return user_predictions + len(images) + 1 <= 5

models_dir = os.path.join(os.path.dirname(os.path.abspath(__name__)), "ml_models")
blip_processor = pickle.load(open(os.path.join(models_dir, "blip_processor.pkl"), "rb"))
blip_model = pickle.load(open(os.path.join(models_dir, "blip_model.pkl"), "rb"))
git_processor = pickle.load(open(os.path.join(models_dir, "git_processor.pkl"), "rb"))
git_model = pickle.load(open(os.path.join(models_dir, "git_model.pkl"), "rb"))

def is_valid_url(url):
    try:
        result = urlparse(url)
        return result.scheme in ['http', 'https', 'data']
    except ValueError:
        return False

def decode_base64_data(name):
    base64_data = name.split(',')[1]
    padding = len(base64_data) % 4
    if padding == 1:
        raise ValueError('Invalid base64 string')
    elif padding > 1:
        base64_data += '=' * (4 - padding)
    return base64.b64decode(base64_data)

def image_conv(name, image_data=None):
    url = name[0] if isinstance(name, tuple) else name
    if is_valid_url(url):
        if url.startswith('data:'):
            image_data = decode_base64_data(url)
        else:
            image_data = requests.get(url).content
        return Image.open(io.BytesIO(image_data)), image_data
    else:
        return Image.open(image_data), None

def generate_filename(form_image, is_url):
    random_hex = secrets.token_hex(8)
    if is_url:
        return random_hex + '.jpg'
    else:
        _, f_ext = os.path.splitext(form_image.filename)
        return random_hex + f_ext

def save_image(form_image, is_url):
    picture_fn = generate_filename(form_image, is_url)
    image = form_image[0] if is_url and isinstance(form_image, tuple) else form_image
    i = Image.open(image) if not is_url else image_conv(image)[0]
    picture_path = os.path.join(current_app.root_path, 'static/uploads', picture_fn)
    output_size = (500,500)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

def process_model(raw_image, model, processor, generator):
    if model == 'blip':
        inputs = processor(raw_image.convert('RGB'), return_tensors="pt")
        out = generator.generate(**inputs)
        return re.sub(r'\baraf\w*', '', processor.decode(generator.generate(**inputs)[0], skip_special_tokens=True))
    elif model == 'git':
        pixel_values = processor(images=raw_image, return_tensors="pt").pixel_values
        generated_ids = generator.generate(pixel_values=pixel_values, max_length=50)
        return processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

def generate_caption(model, filename, raw_image):
    if model in ['blip', 'git']:
        caption = process_model(raw_image, model, blip_processor if model == 'blip' else git_processor, blip_model if model == 'blip' else git_model)
    else:
        flash("Invalid model selection!","danger")
        caption = ''
    return caption


import concurrent.futures

def process_single_image(image_pred, selected_models, app):
    with app.app_context():
        if image_pred.filename:  # check if the file is not empty
            img_saved = save_image(image_pred, False)
            if image_pred.filename and image_pred.mimetype:
                image_filename = secure_filename(image_pred.filename)
                raw_image, _ = image_conv(image_filename, image_pred)
                captions = process_image(selected_models, image_filename, raw_image)
                return image_filename, captions, img_saved
    return None

def process_images(images, selected_models, app):
    captions = {}
    img_saved = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_single_image, image_pred, selected_models, app) for image_pred in images]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                image_filename, image_captions, image_saved = result
                captions[image_filename] = image_captions
                img_saved.append(image_saved)
    return captions, img_saved

def process_image(selected_models, image_filename, raw_image):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(generate_caption, selected_model, image_filename, raw_image): selected_model for selected_model in selected_models}
        captions = {}
        for future in concurrent.futures.as_completed(futures):
            selected_model = futures[future]
            captions[selected_model] = future.result()
    return captions

def process_url_image(url_image, selected_models):
    raw_image, image_data = image_conv(url_image)
    img_saved_url = save_image((url_image, image_data), True)
    image_filename = 'web_image.jpeg'  # get the filename from the saved image path
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(generate_caption, selected_model, img_saved_url, raw_image): selected_model for selected_model in selected_models}
        captions_url = {}
        for future in concurrent.futures.as_completed(futures):
            selected_model = futures[future]
            captions_url[selected_model] = future.result()
    print(f'captions_url: {captions_url}, img_saved_url: {img_saved_url}')
    return {image_filename: captions_url}, img_saved_url

def save_img_cap(img, name, mimetype, selected_model, num_models_used, caption, author):
    img_cap = ImgCap(
        img=img,
        name=name,
        mimetype=mimetype,
        selected_model=selected_model,
        num_models_used=num_models_used,
        caption=caption,
        author=author
    )
    db.session.add(img_cap)

def save_to_table(img_saved, captions=None, selected_model=None, num_models_used=0):
    try:
        if isinstance(img_saved, list) and isinstance(captions, dict):
            # Handle second type of input
            if not captions:
                flash('No captions to save.', 'warning')
                return False

            for index, (image_filename, caption) in enumerate(captions.items()):
                save_img_cap(img_saved[index], image_filename, 'image/jpg', selected_model, num_models_used, caption[selected_model], current_user)

        elif isinstance(img_saved, dict):
            # Handle first type of input
            for image_filename, data in img_saved.items():
                save_img_cap(data['img_saved'], data['image_filename'], 'image/jpg', data['selected_model'], num_models_used, data['selected_captions'], current_user)

        else:
            flash('Invalid input.', 'danger')
            return False

        db.session.commit()
        flash('Selected captions saved successfully!', 'success')
        return True

    except Exception as e:
        flash('An error occurred while saving captions: ' + str(e), 'danger')
        return False