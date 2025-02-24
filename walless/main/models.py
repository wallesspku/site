import time
from django.db.models import (
    Model, IntegerField, AutoField, ForeignKey, CASCADE, PROTECT, GenericIPAddressField,
    EmailField, CharField, TextField, BigIntegerField, BooleanField, DateField, Index,
    DateTimeField, FloatField
)
import shortuuid

from .constants import MAX_EMAIL_HEADER_LENGTH
from walless_utils.utils import HUAWEI_LINES


def node_uuid():
    return 'N' + shortuuid.uuid()[:7]


def user_uuid():
    return 'U' + shortuuid.uuid()[:7]


def current_unix() -> int:
    return int(time.time())


class Node(Model):
    # by default nodes identifies themselves using IP
    # if uuid is specified in a node, it will be used instead
    node_id = IntegerField(unique=True)

    uuid = CharField(max_length=50, primary_key=True, default=node_uuid)

    deleted = BooleanField(default=False)
    hidden = BooleanField(default=False)
    name = CharField(max_length=50, null=False)
    weight = FloatField(default=1.0)
    properties = CharField(max_length=50, null=True, blank=True)
    tag = CharField(max_length=50, null=False, default='gfw:c')

    ipv4 = GenericIPAddressField(null=True, protocol='IPv4', blank=True)
    ipv6 = GenericIPAddressField(null=True, protocol='IPv6', blank=True)
    port = IntegerField(null=True, default=4430)

    # both are used for remakrs
    idc = TextField(max_length=2048, null=True, default='Unknown', blank=True)
    remarks = TextField(max_length=2048, null=True, blank=True)

    upload = BigIntegerField(null=False, default=0)
    download = BigIntegerField(null=False, default=0)

    # traffic plan; reset day is the day of the month.
    traffic_reset_day = FloatField(null=False, default=1.)
    # traffic unit is GiB.
    traffic_limit = BigIntegerField(null=True, default=None, blank=True)

    def __str__(self):
        return f'<Node {self.node_id} {self.name}>'
    
    def save(self, *args, **kwargs):
        for fie in ['ipv4', 'ipv6', 'remarks', 'idc', 'properties']:
            if getattr(self, fie) == '':
                setattr(self, fie, None)
        super(Node, self).save(*args, **kwargs)


class Mix(Model):
    source = ForeignKey(Node, on_delete=CASCADE, related_name='mix_source')
    target = ForeignKey(Node, on_delete=CASCADE, related_name='mix_target')
    scope = CharField(max_length=30, null=False, default='Jiaoyuwang', choices={k: k for k in HUAWEI_LINES})

    def __str__(self) -> str:
        return f'<Mix {self.source} to {self.target}, {self.scope}>'


class User(Model):
    user_id = IntegerField(primary_key=True, unique=True)
    enabled = BooleanField(default=True)
    email = EmailField(max_length=50, null=False, unique=True)
    username = CharField(max_length=50, null=False)
    password = CharField(max_length=50, null=False)
    uuid = CharField(max_length=50, null=False, default=user_uuid, unique=True)
    tag = CharField(max_length=15, null=True)
    # all 3 fields are defined using unix timestamp
    reg_time = IntegerField(null=False, default=current_unix)
    last_activity = IntegerField(null=False, default=current_unix)
    last_change = IntegerField(null=False, default=current_unix)
    last_rotation = IntegerField(null=True, default=current_unix)
    # unit: byte
    upload = BigIntegerField(null=False, default=0)
    download = BigIntegerField(null=False, default=0)
    balance = BigIntegerField(null=False, default=(20 * 2**30))
    # remarks
    remarks = TextField(max_length=2048, null=True, blank=True)


    class Meta:
        indexes = [
            Index(fields=["email"]),
            Index(fields=["uuid"]),
            Index(fields=["last_change"]),
            Index(fields=['enabled']),
        ]

    def __str__(self):
        return f'<user {self.user_id} {self.email}>'
    
    def save(self, *args, **kwargs):
        for fie in ['remarks', 'tag']:
            if getattr(self, fie) == '':
                setattr(self, fie, None)
        super(User, self).save(*args, **kwargs)


class Probe(Model):
    ip = GenericIPAddressField(null=False)
    port = IntegerField(null=False)
    probe_result = IntegerField(null=False)
    ts = IntegerField(null=False, default=current_unix, )

    class Meta:
        indexes = [Index(fields=['ts'])]


class Registration(Model):
    reg_id = AutoField(primary_key=True)
    ts = IntegerField(null=False, default=current_unix)
    email_header = TextField(max_length=MAX_EMAIL_HEADER_LENGTH, null=False)
    receiver = EmailField(max_length=50, null=True)
    sender = EmailField(max_length=50, null=True)
    status = CharField(max_length=10, null=True)

    class Meta:
        indexes = [Index(fields=['ts'])]


class Relay(Model):
    relay_id = AutoField(primary_key=True)
    name = CharField(max_length=50, null=False)
    # use node id instead of node uuid
    source = ForeignKey(Node, null=False, on_delete=PROTECT, related_name='relay_source')
    target = ForeignKey(Node, null=False, on_delete=PROTECT, related_name='relay_target')
    tunnel = CharField(max_length=50, null=True, blank=True)
    tag = CharField(max_length=50, null=True, blank=True)
    hidden = BooleanField(default=False)
    properties = CharField(max_length=50, null=True, blank=True)
    port = IntegerField(null=False, default=5101)

    def __str__(self):
        return f'<Relay {self.relay_id} from {self.source} to {self.target}>'
    
    def save(self, *args, **kwargs):
        for fie in ['tunnel', 'tag', 'properties']:
            if getattr(self, fie) == '':
                setattr(self, fie, None)
        super(Relay, self).save(*args, **kwargs)


class Sublog(Model):
    sub_id = AutoField(primary_key=True)
    user = ForeignKey(User, on_delete=CASCADE, related_name='user_sublog')
    ts = IntegerField(null=False, default=current_unix)
    ip = GenericIPAddressField(null=True)
    remarks = CharField(max_length=45, null=True)
    proxy_group = CharField(max_length=10, null=True)

    class Meta:
        indexes = [Index(fields=['ts'])]


class Traffic(Model):
    ut_id = AutoField(primary_key=True)
    ut_date = DateField(null=False)
    node = ForeignKey(Node, on_delete=PROTECT, related_name='node')
    user = ForeignKey(User, on_delete=CASCADE, related_name='user')
    upload = BigIntegerField(null=False, default=0)
    download = BigIntegerField(null=False, default=0)

    class Meta:
        indexes = [
            Index(fields=['node', 'user'], name="node_user"),
            Index(fields=['node', 'ut_date'], name="node_date"),
            Index(fields=['node'], name="node"),
            Index(fields=['ut_date'], name="date"),
            Index(fields=['node', 'user', 'ut_date'], name="node_user_date"),
        ]
    
    def __str__(self):
        return f'<Traffic {self.ut_date} {self.user} {self.node}>'


class UserTraffic(Model):
    # Traffic with node reduced
    user_traffic_id = AutoField(primary_key=True)
    ut_date = DateField(null=False)
    user = ForeignKey(User, on_delete=CASCADE)
    upload = BigIntegerField(null=False, default=0)
    download = BigIntegerField(null=False, default=0)

    class Meta:
        indexes = [
            Index(fields=['ut_date'], name="user_traffic_date"),
            Index(fields=['user'], name="user_traffic_user"),
            Index(fields=['user', 'ut_date'], name="user_traffic_user_date"),
        ]
    
    def __str__(self):
        return f'<User Traffic {self.ut_date} {self.user}>'


class NodeTraffic(Model):
    # Traffic with user reduced
    node_traffic_id = AutoField(primary_key=True)
    ut_date = DateField(null=False)
    node = ForeignKey(Node, on_delete=CASCADE)
    upload = BigIntegerField(null=False, default=0)
    download = BigIntegerField(null=False, default=0)

    class Meta:
        indexes = [
            Index(fields=['ut_date'], name="node_traffic_date"),
            Index(fields=['node'], name="node_traffic_node"),
            Index(fields=['node', 'ut_date'], name="node_traffic_node_date"),
        ]
    
    def __str__(self):
        return f'<Node Traffic {self.ut_date} {self.node}>'


class TrafficLog(Model):
    log_id = AutoField(primary_key=True)
    user = ForeignKey(User, on_delete=CASCADE, related_name='user_traffic_log')
    node = ForeignKey(Node, on_delete=PROTECT, related_name='user_traffic_log')
    upload = BigIntegerField(null=False, default=0)
    download = BigIntegerField(null=False, default=0)
    ts = IntegerField(null=False, default=current_unix)

    class Meta:
        indexes = [Index(fields=['ts'])]


class Push(Model):
    push_id = AutoField(primary_key=True)
    dt = DateTimeField(auto_now_add=True)
    lines = TextField(max_length=2048)

    def __str__(self):
        return str(self.t)
