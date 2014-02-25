gitzebo
=======

What is gitzebo?
----------------

gitzebo is a small Python git management web application.


Why Reinvent the Wheel?!
------------------------

GitHub, gitorious, GitLab, and gitolite all exist already.  Why not use one of
these?

The answers come down to requirements:

easy to set up
    I dislike playing with configuration files for hours at a time to get
    software working.  Applications should work with a minimum amount of
    documentation reading.  Applications should work with a minimum amount of
    manual steps required to get them running.  Ideally, installing an
    application and deploying it should take one to three commandline
    invocations.

easy to use
    If an application is slow, unintuitive, or fails to solve a user's problems,
    then it will go unused.

in-house deployment
    I have a bone to pick with software-as-a-service (SaaS).  As a rule,
    I don't like giving up
    my proprietary datasets.  This dislike scales up with business value of
    the data: I dislike the idea of giving up a folder of dog pictures I've
    downloaded from the internet to use as wallpapers.  You'd think it's
    useless, and there's no point to being protective: but even that data can
    be used as a training dataset for artificial intelligences dealing with
    visual classification...   Scale it up to source code, configuration
    management, and monitoring?  Those three are the absolute keys to your
    IT kingdom.  My source code management solution will not be SaaS.

The four de-facto solutions each violated one of these requirements flagrantly:

GitHub
    GitHub is software-as-a-service.

gitorious
    gitorious is not easy to set up.
    Deployment on RHEL/CentOS 6 is a pain. `You can read more here.
    <http://famousphil.com/blog/2011/06/installing-gitorious-on-centos-5-6-x64>`_
    I gave up on this approach after a while.

GitLab
    GitLab was not easy to use due to performance issues.
    I got GitLab running in a VM with 1GB of memory and a dedicated core.  Its
    performance with two users was slow enough to regularly invoke vulgarities.
    I don't know if I missed some key setting, but we flagged it a no-go.

gitolite
    gitolite also failed the ease-of-use test.
    gitolite does not have a web application for management built in, so I'd
    have to add one to meet my requirements.  As such, it's more of a library
    or back-end than a full-blown application.  It being written in Perl and
    not having a well-defined API made me extremely nervous.


How? (Deployment)
-----------------

.. todo:: Document deployment!
