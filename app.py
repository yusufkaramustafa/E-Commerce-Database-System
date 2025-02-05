from flask import Flask, jsonify
from config import Config
from db import close_db
from flask_jwt_extended import JWTManager
from flasgger import Swagger
import yaml
import os
import json

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['DEBUG'] = True  # Enable debug mode

    # Initialize JWT
    jwt = JWTManager(app)

    # Load the main Swagger YAML file
    swagger_path = os.path.join(os.path.dirname(__file__), 'docs', 'swagger.yaml')
    with open(swagger_path, 'r') as f:
        swagger_template = yaml.safe_load(f)
        
    # Initialize Swagger
    swagger = Swagger(app, template=swagger_template)
    
    # Register teardown function for closing the DB connection
    app.teardown_appcontext(close_db)

    # Import and register blueprints
    from auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from routes.product import product_bp
    app.register_blueprint(product_bp, url_prefix='/products')
    
    from routes.user import user_bp
    app.register_blueprint(user_bp, url_prefix='/users')
    
    from routes.order import order_bp
    app.register_blueprint(order_bp, url_prefix='/orders')

    from routes.cart import cart_bp
    app.register_blueprint(cart_bp, url_prefix='/cart')
    
    from routes.product_manufacturer import product_manufacturer_bp
    app.register_blueprint(product_manufacturer_bp, url_prefix='/product_manufacturers')

    from routes.manufacturer import manufacturer_bp
    app.register_blueprint(manufacturer_bp, url_prefix='/manufacturers')
    
    from routes.review import review_bp
    app.register_blueprint(review_bp, url_prefix='/reviews')
    
    from routes.payment import payment_bp
    app.register_blueprint(payment_bp, url_prefix='/payments')
    
    from routes.shipping import shipping_bp
    app.register_blueprint(shipping_bp, url_prefix='/shippings')
    
    from routes.address import address_bp
    app.register_blueprint(address_bp, url_prefix='/addresses')

    # Saving Swagger as JSON
    @app.route('/export-swagger', methods=['GET'])
    def export_swagger():
        swagger_spec = swagger.get_apispecs()
        
        if isinstance(swagger_spec, str):
            swagger_spec = json.loads(swagger_spec)
        
        output_path = os.path.join(os.path.dirname(__file__), 'docs', 'exported_swagger.json')
        with open(output_path, 'w') as f:
            json.dump(swagger_spec, f, indent=4) 
        
        return jsonify({"message": "Swagger specification exported successfully", "file_path": output_path})
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run()