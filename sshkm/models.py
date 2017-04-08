from django.db import models
from django.utils import timezone

class Setting(models.Model):
    name = models.CharField(max_length=100, unique=True)
    value = models.TextField(null=True, blank=True)

class Group(models.Model):
    name = models.CharField(max_length=191, unique=True)
    description = models.CharField(max_length=191, null=True, blank=True)
    members = models.ManyToManyField('Key', through='KeyGroup', blank=True)

class Host(models.Model):
    STATE_PENDING = 0
    STATE_SUCCESS = 1
    STATE_FAILURE = 2
    STATE_NOTHING_TO_DEPLOY = 3

    STATE_DESC_MAP = [
        "PENDING",
        "SUCCESS",
        "FAILURE",
        "NOTHING TO DEPLOY",
    ]

    name = models.CharField(max_length=191, unique=True)
    superuser = models.CharField(max_length=191, null=True, blank=True)
    description = models.CharField(max_length=191, null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    last_status = models.DateTimeField(null=True, blank=True)
    error_msg = models.TextField(null=True, blank=True)

    def saveStatus(self, status):
        self.status = status
        self.last_status = timezone.now()
        self.save()

    def saveError(self, error_msg):
        self.status = Host.STATE_FAILURE
        self.last_status = timezone.now()
        self.error_msg = error_msg
        self.save()

    def getStatusDesc(self):
        if self.status != None and self.status < len(Host.STATE_DESC_MAP) and self.status >= 0:
            return Host.STATE_DESC_MAP[self.status]

        return ""

    def getTitleAttrValue(self):
        if self.status == Host.STATE_FAILURE:
            return self.getStatusDesc()+" "+str(self.last_status)+" "+self.error_msg

        return self.getStatusDesc()+" "+str(self.last_status)

    def toJson(self):
        if self.status == Host.STATE_FAILURE:
            return {"id": self.id, "status": self.status, "last_status": self.last_status, "error_msg": self.error_msg}

        return {"id": self.id, "status": self.status, "last_status": self.last_status}

class Osuser(models.Model):
    name = models.CharField(max_length=191, unique=True)
    home = models.CharField(max_length=191, null=True, blank=True)
    description = models.CharField(max_length=191, null=True, blank=True)

class Key(models.Model):
    name = models.CharField(max_length=191, unique=True)
    description = models.CharField(max_length=191, null=True, blank=True)
    firstname = models.CharField(max_length=191, null=True, blank=True)
    lastname = models.CharField(max_length=191, null=True, blank=True)
    email = models.EmailField(max_length=191, null=True, blank=True)
    publickey = models.TextField(null=True, blank=True)
    member_of = models.ManyToManyField('Group', through='KeyGroup', blank=True)

class KeyGroup(models.Model):
    key = models.ForeignKey('Key', on_delete=models.CASCADE)
    group = models.ForeignKey('Group', on_delete=models.CASCADE)

class Permission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    osuser = models.ForeignKey(Osuser, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("group", "host", "osuser")
