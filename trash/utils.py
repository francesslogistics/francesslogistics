from .models import TrashedItem


def move_to_trash(instance, item_type, name, serializer_class, deleted_by=None):
    """
    Snapshot `instance` into TrashedItem and delete the original row.
    `serializer_class` is used to produce a faithful, restorable snapshot.
    `deleted_by` should be the requesting user — each account only ever
    sees the items it personally deleted (see TrashedItemViewSet.get_queryset).
    """
    data = serializer_class(instance).data
    TrashedItem.objects.create(
        item_type=item_type,
        name=name,
        original_id=str(instance.pk),
        data=data,
        deleted_by=deleted_by,
    )
    instance.delete()
