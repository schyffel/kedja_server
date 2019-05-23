
# Development notes

Things to keep in mind when hacking on this.


## Gotchas and problems

1. Cornice doesn't bind or instantiate schemas.
This means that any schema used **must not use colander.deferred** 
decorator. Use after_bind to add validators instead

2. Most validators that depend on context won't work with cornice, 
since it doesn't bind schemas. Add any such validater with the method
**after_bind**, since it will never get exectued by Cornice views.

3. Cornice doesn't care about the Pyramid root factory.
We need to re-register it if it's supposed to be used.
So don't trust **context** within Cornice views.

4. Special validators or Schemas can't be registered for 
class views as default, since Cornice will use that schema for 
the automatic options view for preflight requests too, 
causing them to fail.


## Resources

The term is used in Pyramid for something that's attached to the resource 
tree in traversal. Meaing a persistent resource that can be looked up via
a URL, like /users/jane

https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/resources.html

In this project the term is used the same way as in Pyramid.


However, since we depend on Cornice, where resource is really a view 
registration with methods. So when somethings decorated with @resource
within views, that refers to a Cornice resource:

https://cornice.readthedocs.io/en/latest/resources.html
