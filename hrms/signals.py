from django.db.models.signals import post_save
from django.dispatch import receiver
from hrms.models import Leave
from hrms.admin import changeStatus

@receiver(post_save, sender=Leave)
def leave_post_save(sender, instance, **kwargs):
    changeStatus(instance)