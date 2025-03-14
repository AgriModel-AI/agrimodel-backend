# scheduler.py
import logging
import time
from flask_apscheduler import APScheduler
from flask_mail import Message
from datetime import datetime, timedelta
from sqlalchemy import and_
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import atexit

# Initialize extensions
scheduler = APScheduler()

def send_subscription_email(mail, user, days_remaining=None, is_expired=False):
    """Send subscription notification emails with retry logic"""
    if is_expired:
        subject = "Your subscription has expired"
        body = f"""
        Hello {user.username},
        
        Your subscription has expired. You no longer have access to premium features.
        
        To restore your access, please renew your subscription from your mobile.
        
        Thank you,
        AgriModel Team
        """
    else:
        subject = f"Your subscription expires in {days_remaining} day{'s' if days_remaining != 1 else ''}"
        body = f"""
        Hello {user.username},
        
        Your subscription will expire in {days_remaining} day{'s' if days_remaining != 1 else ''}.
        
        {'Your subscription will renew automatically.' if user.subscriptions[0].autoRenew else 'Please renew your subscription to maintain access to premium features.'}
        
        Thank you,
        AgriModel Team
        """
    
    return send_with_retry(mail, user.email, subject, body)

def send_with_retry(mail, recipient, subject, body, max_retries=3):
    """Send email with retry mechanism"""
    for attempt in range(max_retries):
        try:
            msg = Message(
                subject=subject,
                recipients=[recipient],
                body=body
            )
            mail.send(msg)
            logging.info(f"Email sent to {recipient}")
            return True
        except Exception as e:
            logging.error(f"Attempt {attempt+1} failed to send email to {recipient}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retrying
    
    logging.error(f"Failed to send email to {recipient} after {max_retries} attempts")
    return False

def with_distributed_lock(redis_client, lock_timeout=60):
    """Decorator for distributed locking using Redis"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            lock_name = f"scheduler_lock:{func.__name__}"
            lock = redis_client.lock(lock_name, timeout=lock_timeout)
            
            if lock.acquire(blocking=False):
                try:
                    return func(*args, **kwargs)
                finally:
                    try:
                        lock.release()
                    except:
                        logging.error(f"Failed to release lock {lock_name}")
            else:
                logging.info(f"Task {func.__name__} already running elsewhere")
        return wrapper
    return decorator

def init_scheduler(app, mail, db, User, UserSubscription, redis_client=None):
    """Initialize the scheduler with improved features"""
    # Configure scheduler with persistent job store
    scheduler_jobstore = {
        'default': SQLAlchemyJobStore(url=app.config.get('SCHEDULER_DATABASE_URI', 
                                             app.config.get('SQLALCHEMY_DATABASE_URI')))
    }
    
    # Get scheduler configuration from app config
    check_hour = app.config.get('SUBSCRIPTION_CHECK_HOUR', 9)
    check_minute = app.config.get('SUBSCRIPTION_CHECK_MINUTE', 0)
    expiry_hour = app.config.get('SUBSCRIPTION_EXPIRY_HOUR', 0)
    expiry_minute = app.config.get('SUBSCRIPTION_EXPIRY_MINUTE', 5)
    heartbeat_minutes = app.config.get('SCHEDULER_HEARTBEAT_MINUTES', 60)
    
    # Distributed lock decorator if Redis is available
    lock_decorator = with_distributed_lock(redis_client) if redis_client else lambda f: f
    
    @scheduler.task('cron', id='check_expiring_subscriptions', hour=check_hour, minute=check_minute)
    @lock_decorator
    def check_expiring_subscriptions():
        """Check for subscriptions expiring in 3 or 1 days"""
        start_time = time.time()
        emails_sent = 0
        
        with app.app_context():
            now = datetime.utcnow()
            three_days_ahead = now + timedelta(days=3)
            one_day_ahead = now + timedelta(days=1)
            
            # Find subscriptions expiring in 3 days
            three_day_subs = UserSubscription.query.filter(
                and_(
                    UserSubscription.isActive == True,
                    UserSubscription.endDate >= three_days_ahead.replace(hour=0, minute=0, second=0),
                    UserSubscription.endDate <= three_days_ahead.replace(hour=23, minute=59, second=59)
                )
            ).all()
            
            # Find subscriptions expiring in 1 day
            one_day_subs = UserSubscription.query.filter(
                and_(
                    UserSubscription.isActive == True,
                    UserSubscription.endDate >= one_day_ahead.replace(hour=0, minute=0, second=0),
                    UserSubscription.endDate <= one_day_ahead.replace(hour=23, minute=59, second=59)
                )
            ).all()
            
            # Fetch all users in a single query for 3-day notifications
            if three_day_subs:
                three_day_user_ids = [sub.userId for sub in three_day_subs]
                three_day_users = {user.userId: user for user in User.query.filter(User.userId.in_(three_day_user_ids)).all()}
                
                # Send 3-day notifications
                for subscription in three_day_subs:
                    user = three_day_users.get(subscription.userId)
                    if user:
                        if send_subscription_email(mail, user, days_remaining=3):
                            emails_sent += 1
            
            # Fetch all users in a single query for 1-day notifications
            if one_day_subs:
                one_day_user_ids = [sub.userId for sub in one_day_subs]
                one_day_users = {user.userId: user for user in User.query.filter(User.userId.in_(one_day_user_ids)).all()}
                
                # Send 1-day notifications
                for subscription in one_day_subs:
                    user = one_day_users.get(subscription.userId)
                    if user:
                        if send_subscription_email(mail, user, days_remaining=1):
                            emails_sent += 1
            
            duration = time.time() - start_time
            logging.info(f"Subscription check completed in {duration:.2f} seconds. Sent {emails_sent} emails.")
            
    @scheduler.task('cron', id='process_expired_subscriptions', hour=expiry_hour, minute=expiry_minute)
    @lock_decorator
    def process_expired_subscriptions():
        """Process expired subscriptions and handle auto-renewals"""
        start_time = time.time()
        processed = 0
        renewed = 0
        deactivated = 0
        
        with app.app_context():
            now = datetime.utcnow()
            
            # Find expired subscriptions
            expired_subs = UserSubscription.query.filter(
                and_(
                    UserSubscription.isActive == True,
                    UserSubscription.endDate < now
                )
            ).all()
            
            # Fetch all users in a single query
            if expired_subs:
                user_ids = [sub.userId for sub in expired_subs]
                users = {user.userId: user for user in User.query.filter(User.userId.in_(user_ids)).all()}
                
                # Process each subscription
                for subscription in expired_subs:
                    user = users.get(subscription.userId)
                    processed += 1
                    
                    if subscription.autoRenew:
                        try:
                            # Handle auto-renewal logic here
                            # This would typically involve payment processing
                            if subscription.subscriptionType == 'monthly':
                                subscription.extend_subscription(months=1)
                            else:  # yearly
                                subscription.extend_subscription(months=12)
                            renewed += 1
                            logging.info(f"Auto-renewed subscription for user {user.username if user else subscription.userId}")
                        except Exception as e:
                            logging.error(f"Failed to renew subscription {subscription.id}: {str(e)}")
                            # Mark as inactive if renewal fails
                            subscription.isActive = False
                            deactivated += 1
                            # Notify user of failed renewal
                            if user:
                                send_subscription_email(mail, user, is_expired=True)
                    else:
                        # Mark subscription as inactive
                        subscription.isActive = False
                        deactivated += 1
                        # Send expiration notification
                        if user:
                            send_subscription_email(mail, user, is_expired=True)
                
                # Commit changes to database
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Database error while processing subscriptions: {str(e)}")
            
            duration = time.time() - start_time
            logging.info(f"Processed {processed} expired subscriptions in {duration:.2f} seconds. "
                         f"Renewed: {renewed}, Deactivated: {deactivated}")
    
    @scheduler.task('interval', id='scheduler_heartbeat', minutes=heartbeat_minutes)
    def scheduler_heartbeat():
        """Send a heartbeat to confirm scheduler is running"""
        with app.app_context():
            logging.info("Scheduler heartbeat: still running")
            # Could also update a database record or send a notification
    
    # Configure scheduler
    scheduler.api_enabled = app.config.get('SCHEDULER_API_ENABLED', False)
    
    # Initialize with job stores if persistence is needed
    if app.config.get('SCHEDULER_PERSISTENT', True):
        scheduler.scheduler.configure(jobstores=scheduler_jobstore)
    
    # Register graceful shutdown
    def shutdown_scheduler():
        scheduler.shutdown(wait=True)
        logging.info("Scheduler shutdown complete")
    
    atexit.register(shutdown_scheduler)
    
    # Initialize and start scheduler
    scheduler.init_app(app)
    scheduler.start()
    logging.info("Scheduler started successfully")