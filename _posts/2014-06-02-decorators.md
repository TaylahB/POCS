---
layout: post
title: Python Decorators: Logger and Config in POCS
permalink: python-decorators
category: examples
tags: python decorators config logging panoptes
---

# Python Decorators {#python-decorators}
## Logger and Config in POCS

We are going to look at an example of python decorators by implementing a fairly common requirement for a project: logging and configuration. The goal is to have an easy-to-use set of methods that can be applied to any module within our project and allow a developer to have access to the projects logging and configuration settings. The decorators should be fairly black-box so that the developer doesn't need to worry about internals. Since the `Config` class is loaded as part of the `Logger` loading, so the `Logger` class can be configured from the config file, we are going to take a look at `Config` first.

Before we begin, however, here is what we want our developers to be able to do:
``` 
import panoptes.utils.logger as logger
import panoptes.utils.config as config

@logger.has_logger
class AbstractMount():
    def __init__(self):        
        # Write something to the log
        self.logger.info('Creating AbstractMount')
        self.logger.debug('Debug Level info for AbstractMount')


@logger.set_log_level('debug')
@logger.has_logger
@config.has_config
class Mount(AbstractMount):
    def __init__(self, *args, **kwargs):
        # Get the mount type from the config
        type = self.config.get('mount').get('type')
        
        # Write something to the log
        self.logger.info('Creating Mount: {}'.format(type))
		self.logger.debug('Debug Level info for Mount')

        super().__init__(*args, **kwargs)
```
> **CODE NOTE:**
> 
> - We've already done a check for the `'mount'` key in the config
> - `self.logger` has access to all the log levels: `critical`, `error`, `warning`, `info`, `debug`

#### Decorators
A brief word about python decorators. Decorators allow you to apply a function, or set of functions, to a class or method. The same thing could be done with OO programming and some cleverness. For instance, in POCS, almost everything is driven by the `Observatory` class, so we could make it our base class, read the configuration in during the `Observatory` init, and then have everything inherit from the `Observatory` class, but this is messy and begins to pollute our namespace. The advantage of a decorator is that the functionality contained within the decorator is decoupled from a specific class, giving much more flexibility. Also, the logic contained within the decorators is usually separate business logic from that contained within just a specific module, class, or method. So while our `Observatory` may need to log, it's core logic should not contain logging methods, but rather methods like `start_slewing` and `check_weather`, which relate to the business of an observatory. The `Observatory` class is then 'decorated' with the other functionality. [^perl-roles]

#### Config Class

#### Logger Class

> [@wtgee](https://github.com/wtgee "@wtgee")

[^perl-roles]: In Perl, Decorators are called [Roles](http://perldoc.perl.org/perlootut.html#Roles), and a Role is said to be "applied" to a class or a class "consumes" a Role, which has more functional meaning to me than a Decorator "decorating" a class.

