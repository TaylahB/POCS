---
layout: post
title: Hello World
---

# Hello World

This is a test. I would like code and MathJax working.

~~~ python
import panoptes.utils.logger as logger

@logger.has_logger
class FooBar():
  """ This class is FooBar! """
  def __init__(self):
    self.logger.info('Inside Class')
~~~

The equation for inline math \( z = 1.4 \) is working if you use \\( and \\).

$$ z = \frac{\lambda_{obs} - \lambda_{em}}{\lambda_{em}} $$

Interesting.
