import os
from flask import url_for, render_template, request, abort, redirect
from flask_admin import helpers as admin_helpers
from flask_login import current_user, login_required
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.utils import encrypt_password
from flask_wtf import Form
from wtforms.ext.sqlalchemy.orm import model_form
from helpers import get_need_fields_for_application, get_fields_validators
from lang.ru_RU import user_labels
from main import app, db, admin
from models import Role, User, MyModelView, Event, Application

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/camp')
def camp():
    last_event = Event.query.first()
    return render_template("camp.html", event=last_event)


@app.route('/camp/take_part', methods=["GET", "POST"])
@login_required
def takepart_camp():
    last_event = Event.query.first()

    fields = get_need_fields_for_application(current_user)
    validators = get_fields_validators(fields)

    take_part_form = model_form(User, Form, only=fields, field_args=validators)
    take_part_form = take_part_form(name='take_part')

    if not current_user.has_role('участник'):
        user = user_datastore.find_user(email=current_user.email)
        user_datastore.add_role_to_user(user, Role(name="участник"))
        db.session.commit()

    if request.method == 'POST':
        take_part_form = model_form(User, Form, only=fields, field_args=validators)
        take_part_form = take_part_form(request.form)

        if take_part_form.validate():
            return redirect("/")

    return render_template("take_part.html", event=last_event, user_form=take_part_form)


@app.before_request
def check_for_admin(*args, **kw):
    if request.path == '/admin/':
        if not current_user.is_active or not current_user.is_authenticated or not current_user.has_role('superuser'):
            return abort(404)


@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )


admin.add_view(MyModelView(Role, db.session))
admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Event, db.session))
admin.add_view(MyModelView(Application, db.session))

app_dir = os.path.realpath(os.path.dirname(__file__))
database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])


def build_sample_db():
    """
    Function for debug only
    """

    import string
    import random

    db.drop_all()
    db.create_all()

    with app.app_context():
        user_role = Role(name='user')
        super_user_role = Role(name='superuser')
        db.session.add(user_role)
        db.session.add(super_user_role)
        db.session.commit()

        test_user = user_datastore.create_user(
            first_name='Admin',
            email='admin',
            password=encrypt_password('admin'),
            roles=[user_role, super_user_role]
        )

        first_names = [
            'Harry', 'Amelia', 'Oliver', 'Jack', 'Isabella', 'Charlie', 'Sophie', 'Mia',
            'Jacob', 'Thomas', 'Emily', 'Lily', 'Ava', 'Isla', 'Alfie', 'Olivia', 'Jessica',
            'Riley', 'William', 'James', 'Geoffrey', 'Lisa', 'Benjamin', 'Stacey', 'Lucy'
        ]
        last_names = [
            'Brown', 'Smith', 'Patel', 'Jones', 'Williams', 'Johnson', 'Taylor', 'Thomas',
            'Roberts', 'Khan', 'Lewis', 'Jackson', 'Clarke', 'James', 'Phillips', 'Wilson',
            'Ali', 'Mason', 'Mitchell', 'Rose', 'Davis', 'Davies', 'Rodriguez', 'Cox', 'Alexander'
        ]

        for i in range(len(first_names)):
            tmp_email = first_names[i].lower() + "." + last_names[i].lower() + "@example.com"
            tmp_pass = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(10))
            user_datastore.create_user(
                first_name=first_names[i],
                last_name=last_names[i],
                email=tmp_email,
                password=encrypt_password(tmp_pass),
                roles=[user_role, ]
            )
        db.session.commit()
    return


if __name__ == '__main__':
    app.run(debug=True)
