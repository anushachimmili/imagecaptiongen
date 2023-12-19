from datetime import datetime, timedelta
import os
import re 
from imagecaptiongen import db 
from flask import (render_template, url_for, flash, jsonify, g,
                   redirect, request, abort, Blueprint, Response, current_app)
from flask_login import current_user, login_required
from imagecaptiongen.models import ImgCap
from imagecaptiongen.captions.forms import PredictForm, UpdateCaptionForm
from imagecaptiongen.captions.utils import (is_valid_url, check_prediction_limit, 
                                            process_images, process_url_image, save_to_table)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import or_, func


captions = Blueprint('captions', __name__)


@captions.before_request
def before_request():
    try:
        if current_user.is_authenticated:
            blip_usr_ratings = ImgCap.query.filter(ImgCap.selected_model=='blip', ImgCap.rating>0).all()
            git_usr_ratings = ImgCap.query.filter(ImgCap.selected_model=='git', ImgCap.rating>0).all()
            blip_usr_avg = sum([r.rating for r in blip_usr_ratings]) / len(blip_usr_ratings) if blip_usr_ratings else 0
            git_usr_avg = sum([r.rating for r in git_usr_ratings]) / len(git_usr_ratings) if git_usr_ratings else 0
            multiple_model_cap_cnt = ImgCap.query.filter(ImgCap.num_models_used==2).count()
            blip_model_sel_cnt = ImgCap.query.filter(ImgCap.num_models_used==2,ImgCap.selected_model=='blip').count()
            git_model_sel_cnt = ImgCap.query.filter(ImgCap.num_models_used==2,ImgCap.selected_model=='git').count()
            blip_score = (blip_model_sel_cnt / (multiple_model_cap_cnt or 1))
            git_score = (git_model_sel_cnt / (multiple_model_cap_cnt or 1))
            max_avg = 6
            g.blip_avg = (blip_usr_avg + blip_score) / max_avg * 5
            g.git_avg = (git_usr_avg + git_score) / max_avg * 5
            scores = {'BLIP': round(10*blip_score),'GIT': round(10*git_score)}
            g.scored_model = max(scores, key=scores.get)
            g.max_score = max(scores.values())
    except Exception as e:
        print(f"An error occurred: {e}")

@captions.route("/caption/<int:img_id>", methods=['GET', 'POST'])
@login_required
def caption(img_id):
    img = ImgCap.query.get_or_404(img_id)
    if not img:
        return 'Img Not Found!', 404 
    image_file = url_for('static', filename='uploads/'+ img.img)
    return image_file


@captions.route("/user_captions")
def user_captions():
    print(f'request.args: {request.args}')
    date_filter = request.args.get('date')
    custom_date_filter = request.args.get('custom_date')

    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        imgs = ImgCap.query.filter_by(user_id=current_user.id)

        if date_filter == 'today':
            date_filter = datetime.today().date()
            print(f"Date filter: {date_filter}")
            imgs = imgs.filter(func.date(ImgCap.date_uploaded) == date_filter)
            print(f"Images: {imgs.all()}")
        elif date_filter == 'last_week':
            one_week_ago = datetime.today().date() - timedelta(days=7)
            imgs = imgs.filter(func.date(ImgCap.date_uploaded) >= one_week_ago)
        elif date_filter == 'custom' and custom_date_filter:
            custom_date_filter = datetime.strptime(custom_date_filter, '%Y-%m-%d').date()
            imgs = imgs.filter(func.date(ImgCap.date_uploaded) == custom_date_filter)

        imgs = imgs.order_by(ImgCap.date_uploaded.desc()).paginate(page=page, per_page=2)
        num_predictions = imgs.total
    else:
        imgs = ImgCap.query.limit(2).all()
        num_predictions = len(imgs)

    return render_template('captions/user_captions.html', title='User Captions', 
                            imgs=imgs, num_predictions=num_predictions)


@captions.route("/search", methods=['GET'])
def search():
    query = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    if current_user.is_authenticated:
        imgs = ImgCap.query.filter(or_(ImgCap.name.contains(query), \
                                       ImgCap.caption.contains(query),\
                                       ImgCap.tag.contains(query)))\
                            .filter_by(user_id=current_user.id)\
                            .order_by(ImgCap.date_uploaded.desc())\
                            .paginate(page=page, per_page=2)
    else:
        imgs = ImgCap.query.filter(or_(ImgCap.name.contains(query), ImgCap.caption.contains(query),\
                                       ImgCap.tag.contains(query))).all()
    return render_template('captions/user_captions.html', title='Searched Captions', imgs=imgs)

@captions.route("/caption/delete/<int:img_id>", methods=['POST'])
@login_required
def delete_caption(img_id):
    image = ImgCap.query.get_or_404(img_id)
    if image.author != current_user:
        abort(403)
    picture_path = os.path.join(current_app.root_path, 'static/uploads', image.img)
    print(picture_path)
    if os.path.exists(picture_path):
        os.remove(picture_path)
    db.session.delete(image)
    db.session.commit()
    flash('Image and caption deleted!', 'danger')
    return redirect(url_for('captions.user_captions'))

@captions.route("/caption/update/<int:img_id>", methods=['GET', 'POST'])
@login_required
def update_caption(img_id):
    image = ImgCap.query.get_or_404(img_id)
    if image.author != current_user:
        abort(403)
    form = UpdateCaptionForm()
    if form.validate_on_submit():  # If the form is submitted and valid
        image.caption = form.caption.data  # Update the image's caption
        image.is_user_modified = True  # Update the is_user_modified flag
        image.date_uploaded = datetime.utcnow()  # Update the date uploaded
        db.session.commit()  # Commit the changes to the database
        flash('Caption updated successfully', 'success')
        return redirect(url_for('captions.user_captions'))
    elif request.method == 'GET':
        form.caption.data = image.caption
    return render_template('captions/update_caption.html', title='Update Caption', form=form, image=image)

@captions.route('/caption/rate/<int:img_id>/<int:rating>', methods=['POST'])
@login_required
def rate_caption(img_id, rating):
    print(f"Rate caption called with img_id: {img_id} and rating: {rating}")  # print statement 1
    img = ImgCap.query.get_or_404(img_id)
    print(f"Image fetched from database: {img}")  # print statement 2
    if img.user_id != current_user.id:
        abort(403)
    img.rating = float(rating)
    db.session.commit()
    print(f"Rating updated and committed: {img.rating}")  # print statement 3
    return jsonify({'status': 'success'})

@captions.route('/caption/update_tag/<int:img_id>', methods=['POST'])
@login_required
def update_tag(img_id):
    img = ImgCap.query.get_or_404(img_id)
    img.tag = request.form['tag']
    db.session.commit()
    return redirect(url_for('captions.user_captions'))


@captions.route("/predict", methods=['GET', 'POST'])
@login_required
def predict():
    form = PredictForm()
    if form.is_submitted():
        if form.validate():
            selected_models = request.form.getlist('model')
            images = request.files.getlist('image_pred')
            url_image = form.url_image.data if hasattr(form, 'url_image') else ''
            print(f'url_image: {url_image}')
            print(f'valid url: {is_valid_url(url_image)}')
            if not current_user.is_premium():
                check_user_limit = check_prediction_limit(current_user, images)
                if not check_user_limit:
                    flash('Free users are limited to 5 predictions.', 'warning')
                    return redirect(url_for('main.home'))
            captions, img_saved = ({}, []) if not images else process_images(images, selected_models, current_app._get_current_object())
            print(f'captions: {captions}, img_saved: {img_saved}')
            if is_valid_url(url_image):
                captions_url, img_saved_url = process_url_image(url_image, selected_models)
                print(f'captions_url: {captions_url}, img_saved_url: {img_saved_url}')
                captions.update(captions_url)
                img_saved.append(img_saved_url)
            print(f'captions: {captions}, img_saved: {img_saved}')
            if len(selected_models) == 2:
                return render_template('captions/select_caption.html',  title='Select Captions', captions=captions, img_saved=img_saved)
            elif len(selected_models) == 1:
                save_to_table(img_saved, captions, selected_models[0],num_models_used=1)
                return redirect(url_for('captions.user_captions')) # Save the captions to the database
        else:
            flash('Check your inputs', 'danger')
    return render_template('captions/predict.html',  title='Predict Captions', form=form)


@captions.route("/select_caption", methods=['POST'])
@login_required
def select_caption():
    print(request.form)
    image_data = {}
    for key in request.form.keys():
        match = re.match(r'(\w+)\[(\w+\.\w+)\]', key)
        if match:
            field, image_filename = match.groups()
            if image_filename not in image_data:
                image_data[image_filename] = {}
            for value in request.form.getlist(key):
                image_data[image_filename][field] = value
    print(f"Image Data - {image_data}")
    save_to_table(image_data, num_models_used=2)
    return redirect(url_for('captions.user_captions'))

@captions.route("/download_captions", methods=['GET'])
@login_required
def download_captions():
    format = request.args.get('format', 'csv')  # Default to 'csv' if no format is specified
    if not current_user.is_premium():
        flash('Free users do not have access to download captions.', 'warning')
        return redirect(url_for('main.home'))
    imgcap_data = ImgCap.query.filter_by(author=current_user).all()
    if imgcap_data:
        if format == 'csv':
            csv_data = "Image,Caption\n"
            for item in imgcap_data:
                csv_data += f"{item.name},{item.caption}\n"
            response = Response(csv_data, content_type='text/csv')
            response.headers['Content-Disposition'] = 'attachment; filename=image_captions.csv'
        elif format == 'pdf':
            pdf = SimpleDocTemplate("image_captions.pdf", pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            for item in imgcap_data:
                img_path = os.path.join(os.path.dirname(__file__), "static/uploads", item.img)
                print(f"Trying to open image at: {img_path}")
                img = Image(img_path, width=100, height=100)  # Adjust size as needed
                caption = Paragraph(f"<b>Image:</b> <i>{item.name}</i> <br/> <b>Caption:</b> {item.caption}", styles["BodyText"])
                # Create a table with the image and caption in the same row
                table = Table([[img, caption]], colWidths=[170, 300])  # Adjust column widths as needed
                # Create a table style and apply it to the table
                style = TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment
                ])
                table.setStyle(style)
                story.append(table)
                story.append(Spacer(1, 12))  # Add some space between items
            pdf.build(story)
            with open("imgcap_data.pdf", "rb") as f:
                response = Response(f.read(), content_type='application/pdf')
                response.headers['Content-Disposition'] = 'attachment; filename=imgcap_data.pdf'
        else:
            flash('Invalid format specified.', 'danger')
            return redirect(url_for('main.home'))
    else:
        flash('No image caption data found. Create some predictions!', 'warning')
        return redirect(url_for('main.home'))
    return response
