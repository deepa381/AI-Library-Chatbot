from django.db import models

class BaseModel(models.Model):
    """
    Abstract base model that provides self-updating 'created_at' and 'updated_at' fields.
    All application models should inherit from this class.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="The date and time when this record was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when this record was last updated."
    )

    class Meta:
        abstract = True
