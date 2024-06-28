# from django.db import models
# import uuid
# from accounts.models import  WaiterProfile, ClientProfile

# class Tip(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     waiter = models.ForeignKey(WaiterProfile, on_delete=models.CASCADE)
#     client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, null=True)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     date = models.DateTimeField(auto_now_add=True)
#     review = models.TextField(blank=True, null=True)
#     rating = models.IntegerField(blank=True, null=True)

#     def __str__(self):
#         return f"Tip from {self.client.nickname} to {self.waiter.user.username} - {self.amount}"
