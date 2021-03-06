# Welcome to yo-runner's documentation\!

Yo is a Yaml-driven task runner for lazy people. When you're coding, you may
often need to run a long command many times, but you don't want to do all that
typing every time. You don't want to have to remember the options or the flags
every time. You could write a Makefile, but they're annoying. Maybe your
toolkit provides the functionality, if you want to mess with that. You could
use something like gulp or grunt, but that's a lot of overhead. All you really
want is something like directory-specific aliases.

That's where yo comes in. All you do is write a `yo.yaml` that looks something
like this:

``` yaml
run: poetry run flask run
serve-docs: python -m http.server --directory docs/_build
docs: 
  - poetry run sphinx-build docs docs/_build | tee docs/build_errors.txt
  - serve-docs
test: poetry run pytest
```

Now, in that directory you can run `yo run` to run your app, `yo serve-docs` to
serve your documentation folder, `yo docs` to build and serve documentation,
and `yo test` to figure out why your stupid program still isn't working. And
any arguments you pass to the `yo` command will be passed through the task.

Yo can handle single commands, sequential lists, and concurrent lists. Every
command is run on the shell, so pipes and redirects work. There's also support
for environment variables and variables internal to the `yo.yaml` so that you
don't have to type paths more than once. It's lazy all the way down. See
[Usage](usage.md) for more information on how to do all of this.

### Similar projects

  - Sort of close to what Yo does:
      - [Make](https://www.gnu.org/software/make/), if you use `.PHONY` and
        generally don't worry about dependencies
      - [Just](https://github.com/casey/just), probably the closest thing, aims
        to be a less annoying Make
      - NPM, Poetry, probably a bunch of other frameworks have something built
        in that I'm too lazy to learn
  - More heavy-duty:
      - [Gulp](https://gulpjs.com/)
      - [Grunt](https://gruntjs.com/)

## Contents

  - [Usage](usage.md)
  - [API](api.md)

## Indices and tables

  - [genindex](genindex)
  - [modindex](modindex)
  - [search](search)
