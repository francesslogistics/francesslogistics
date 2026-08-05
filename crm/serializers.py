from rest_framework import serializers
from .models import Agent, Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "name", "phone", "email", "is_default"]


class AgentSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(many=True, required=False)

    class Meta:
        model = Agent
        fields = ["id", "slug", "name", "industry", "note", "last_contact", "contacts", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def create(self, validated_data):
        contacts_data = validated_data.pop("contacts", [])
        agent = Agent.objects.create(**validated_data)
        self._sync_contacts(agent, contacts_data)
        return agent

    def update(self, instance, validated_data):
        contacts_data = validated_data.pop("contacts", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if contacts_data is not None:
            instance.contacts.all().delete()
            self._sync_contacts(instance, contacts_data)
        return instance

    @staticmethod
    def _sync_contacts(agent, contacts_data):
        made_default = False
        for c in contacts_data:
            is_default = bool(c.get("is_default")) and not made_default
            if is_default:
                made_default = True
            Contact.objects.create(
                agent=agent,
                name=c.get("name", ""),
                phone=c.get("phone", ""),
                email=c.get("email", ""),
                is_default=is_default,
            )
        if contacts_data and not made_default:
            first = agent.contacts.first()
            if first:
                first.is_default = True
                first.save()
