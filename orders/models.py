from django.db import models
from shop.models import Product

from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from coupons.models import Coupon

# Todo : 결제 관련 기능 임포트
from .iamport import validation_prepare, get_transaction

import time
import random
import hashlib

from django.db.models.signals import post_save

class Order(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)

    # Todo : 할인 관련 필드 추가
    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT, related_name='order_coupon', null=True, blank=True)
    discount = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        ordering = ['-created', ]

    def __str__(self):
        return 'Order {}'.format(self.id)

    def get_total_product(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_total_discount(self):
        return self.get_total_product()*(self.discount/Decimal(100))

    def get_total_cost(self):
        total_cost = self.get_total_product()
        total_discount = self.get_total_discount()
        return total_cost - total_discount


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return '{}'.format(self.id)

    def get_cost(self):
        return self.price * self.quantity


class OrderTransactionManager(models.Manager):
    def create_new(self,order,amount,success=None,transaction_status=None):
        if not order:
            raise ValueError("주문 오류")

        short_hash = hashlib.sha1(str(random.random()).encode('utf-8')).hexdigest()[:2]
        time_hash = hashlib.sha1(str(int(time.time())).encode('utf-8')).hexdigest()[-3:]
        base = str(order.email).split("@")[0]
        key = hashlib.sha1((short_hash + time_hash + base).encode('utf-8')).hexdigest()[:10]

        merchant_order_id = "%s"%(key)
        print(merchant_order_id)
        validation_prepare(merchant_order_id,amount)

        new_trans = self.model(
            order=order,
            merchant_order_id=merchant_order_id,
            amount=amount
        )

        if success is not None:
            new_trans.success = success
            new_trans.transaction_status = transaction_status

        try:
            new_trans.save()
        except Exception as e:
            print("save error",e)

        return new_trans.merchant_order_id

    def validation_trans(self,merchant_order_id):
        result = get_transaction(merchant_order_id)
        if result['status'] == 'paid':
            return result
        else:
            return None


class OrderTransaction(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    merchant_order_id = models.CharField(max_length=120, null=True, blank=True)
    transaction_id = models.CharField(max_length=120, null=True,blank=True)
    amount = models.PositiveIntegerField(default=0)
    transaction_status = models.CharField(max_length=220, null=True,blank=True)
    type = models.CharField(max_length=120,blank=True)
    created = models.DateTimeField(auto_now_add=True,auto_now=False)

    # 디폴트 매니저 대신 우리가 만든 매니저를 연결한다.
    objects = OrderTransactionManager()

    def __str__(self):
        return str(self.order.id)

    class Meta:
        ordering = ['-created']


def new_order_trans_validation(sender, instance, created, *args, **kwargs):
    if instance.transaction_id:
        # iamport에서 실제 결제 정보 확인
        v_trans = OrderTransaction.objects.validation_trans(merchant_order_id=instance.merchant_order_id)

        res_merchant_id = v_trans['merchant_order_id']
        res_imp_id = v_trans['imp_id']
        res_amount = v_trans['amount']

        # iamport에서 결제된 정보와 일치하는 주문을 db에서 확인
        r_trans = OrderTransaction.objects.filter(merchant_order_id = res_merchant_id, transaction_id = res_imp_id,amount = res_amount).exists()

        # 둘중에 하나라도 없으면 비정상 거래
        if not v_trans or not r_trans:
            raise ValueError("비정상 거래입니다.")

# 결제 정보가 생성된 후에 호출할 함수를 연결해준다.
post_save.connect(new_order_trans_validation,sender=OrderTransaction)