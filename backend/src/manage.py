#!/usr/bin/env python
import os
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from main import create_app
from database_postgres import db

# Create app instance
app = create_app()
migrate = Migrate(app, db)
manager = Manager(app)

# Add migration commands
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
