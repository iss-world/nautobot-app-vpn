from django.db import models


class EncryptionAlgorithm(models.Model):
    code = models.CharField(max_length=32, unique=True)
    label = models.CharField(max_length=128)

    def __str__(self):
        return self.label


class AuthenticationAlgorithm(models.Model):
    code = models.CharField(max_length=32, unique=True)
    label = models.CharField(max_length=128)

    def __str__(self):
        return self.label


class DiffieHellmanGroup(models.Model):
    code = models.CharField(max_length=16, unique=True)
    label = models.CharField(max_length=128)

    def __str__(self):
        return self.label
