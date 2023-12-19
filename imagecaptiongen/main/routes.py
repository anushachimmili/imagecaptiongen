from flask import render_template, Blueprint
# from flask import request, flash, redirect, url_for, current_app
from flask_login import current_user
from imagecaptiongen import db
from imagecaptiongen.models import User
# import stripe
# from stripe.error import (CardError, RateLimitError, InvalidRequestError, 
#                            AuthenticationError, APIConnectionError, StripeError)

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    if current_user.is_authenticated:
        return render_template('main/user_home.html', title='User Home')
    else:
        return render_template('main/home.html', title='Home')
    
@main.route('/unsubscribe', methods=['POST'])
def unsubscribe():
  # Get the current user
  user = User.query.get(current_user.id)
  # Update the membership_type
  user.membership_type = 'free'
  # Save the changes
  db.session.commit()
  return 'Success'

@main.route('/subscribe', methods=['POST'])
def subscribe():
  # Get the current user
  user = User.query.get(current_user.id)
  # Update the membership_type
  user.membership_type = 'premium'
  # Save the changes
  db.session.commit()
  return 'Success'


# @main.route('/payment/<membership_type>', methods=['GET', 'POST'])
# def payment(membership_type):
#     if request.method == 'POST':
#         try:
#             customer = stripe.Customer.create(
#                 email=request.form['stripeEmail'],
#                 source=request.form['stripeToken']
#             )

#             charge = stripe.Charge.create(
#                 customer=customer.id,
#                 amount=500,
#                 currency='usd',
#                 description='Premium Membership'
#             )

#             subscription = stripe.Subscription.create(
#                 customer=customer.id,
#                 items=[{'plan': 'Image Caption'}],
#             )

#             flash('Your payment has been processed! You are now a premium member!', 'success')
#             return redirect(url_for('users.login'))
        
#         except CardError as e:
#             # Since it's a decline, CardError will be caught
#             body = e.json_body
#             err  = body.get('error', {})
#             flash(f"Status is: {e.http_status}. Type is: {err.get('type')}. Code is: {err.get('code')}. Message is: {err.get('message')}.")
#         except RateLimitError as e:
#             # Too many requests made to the API too quickly
#             flash("Too many requests made to the API too quickly. Please try again later.")
#         except InvalidRequestError as e:
#             # Invalid parameters were supplied to Stripe's API
#             flash("Invalid parameters were supplied to Stripe's API. Please try again.")
#         except AuthenticationError as e:
#             # Authentication with Stripe's API failed
#             flash("Authentication with Stripe's API failed. Please try again.")
#         except APIConnectionError as e:
#             # Network communication with Stripe failed
#             flash("Network communication with Stripe failed. Please try again.")
#         except StripeError as e:
#             # Display a very generic error to the user, and maybe send yourself an email
#             flash("An error occurred while processing your payment. Please try again.")
#         except Exception as e:
#             # Something else happened, completely unrelated to Stripe
#             flash("An error occurred while processing your payment. Please try again.")

#     return render_template('main/payment.html', title='Payment', key=current_app.config['STRIPE_PUBLIC_KEY'])
