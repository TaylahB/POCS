---
layout: post
title: Hello World
---

# Hello World

This is a test. I would like code and MathJax working.

### Code

Code is done with the following syntax:

`{\% highlight python linenos \%}`   
`Super code goes here`  
`{\% endhighlight \%}`  

{% highlight python linenos %}
import panoptes.utils.logger as logger

@logger.has_logger
class FooBar():
  """ This class is FooBar! """
  def __init__(self):
    self.logger.info('Inside Class')
{% endhighlight %}


### Latex Math

Inline math \\( z = 1.4^2 \\) is done with `\\( ... \\)` while a math block:

$$ z = \frac{\lambda_{obs} - \lambda_{em}}{\lambda_{em}} $$

is done with `$$ ... $$`

Interesting. And ideally not orange.
