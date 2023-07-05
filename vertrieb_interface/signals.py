# from .models import VertriebAngebot
# from django.db.models.signals import pre_save
# from django.dispatch import receiver
# from django.utils import timezone
# from django.core.exceptions import ObjectDoesNotExist
# import datetime
# from dotenv import load_dotenv
# load_dotenv()

# @receiver(pre_save, sender=VertriebAngebot)
# def handle_status_change(sender, instance, **kwargs):
#     print("handle_status_change was called")
#     try:
#         old_instance = sender.objects.get(zoho_id=instance.zoho_id)
#         if old_instance.status != instance.status and instance.status == 'bekommen':
#             current_datetime = datetime.datetime.now()
#             # instance.status_change_date = f"{current_datetime.strftime('%d.%m.%Y')}"

#     except ObjectDoesNotExist:
#         instance.angebot_bekommen_am = timezone.now().date()
