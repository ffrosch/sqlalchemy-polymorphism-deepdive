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

### SELECT IN eager loading

> The strategy emits a SELECT for up to 500 parent primary key values at a time, as thce primary keys are rendered into a large IN expression in the SQL statement. Some databases like Oracle Database have a hard limit on how large an IN expression can be, and overall the size of the SQL string shouldn’t be arbitrarily large.
> [Quelle](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#select-in-loading)


## Technical Reading

- [Writing Select Statements for Inheritance Mappings](https://docs.sqlalchemy.org/en/20/orm/queryguide/inheritance.html#writing-select-statements-for-inheritance-mappings)
