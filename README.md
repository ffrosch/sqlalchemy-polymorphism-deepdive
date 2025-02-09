# SQLAlchemy Polymorphic Associations

## Architectural Choices

### Eager loading of associations
In the context of this project and the use cases the models will always be queried for their associations. To make the sql queries as efficient as possible, it is important that those associations are loaded eagerly.

This requires extra attention for the polymorphic associations, because they will not load eagerly even if all relations are configured to load eagerly.

According to the [SQLAlchemy Docs](https://docs.sqlalchemy.org/en/20/orm/queryguide/inheritance.html#configuring-with-polymorphic-on-mappers) this is best done with the `polymorphic_load: inline` mapper argument on each individual subclass.

**WARN**: It is advised against using the `with_polymorphic` on the Parent (PolymorphicInterface).

```python
class Subclass(PolymorphicInterface):
    __mapper_args__ = {
        "polymorphic_load": "inline",
        }
```
