"""This file is part ike and ipsec crypto options."""

from django.db import models


class EncryptionAlgorithm(models.Model):
    """Model representing an encryption algorithm."""

    code = models.CharField(max_length=32, unique=True)
    label = models.CharField(max_length=128)

    def __str__(self):
        return self.label


class AuthenticationAlgorithm(models.Model):
    """Model representing an authentication algorithm."""

    code = models.CharField(max_length=32, unique=True)
    label = models.CharField(max_length=128)

    def __str__(self):
        return self.label


class DiffieHellmanGroup(models.Model):
    """Model representing a Diffie-Hellman group."""

    code = models.CharField(max_length=16, unique=True)
    label = models.CharField(max_length=128)

    def __str__(self):
        return self.label
