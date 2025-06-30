from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Flipbook(db.Model):
    __tablename__ = 'flipbooks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    pdf_url = db.Column(db.String(500))  # URL do PDF original
    flipbook_url = db.Column(db.String(500))  # URL do flipbook (ex: Issuu)
    embed_code = db.Column(db.Text)  # Código de incorporação
    thumbnail_url = db.Column(db.String(500))  # URL da imagem de capa
    category = db.Column(db.String(50))  # categoria da revista
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'pdf_url': self.pdf_url,
            'flipbook_url': self.flipbook_url,
            'embed_code': self.embed_code,
            'thumbnail_url': self.thumbnail_url,
            'category': self.category,
            'featured': self.featured,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

