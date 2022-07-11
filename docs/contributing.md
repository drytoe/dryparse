# Contributing

```{toctree}
```

## Programming techniques you should keep in mind

### Marking a method as unimplemented but not abstract

```
def method(self):
   ...  # pylint: unnecessary-ellipsis
   raise NotImplementedError
```

## Documentation

- Shell code must be added like this:

````md
```{prompt} bash
   shell commands here
```
````

- When adding python code examples, dryparse objects must link to their
  corresponding documentation:
    
     ```{tabs}
        ```{tab} Correct
        **Source:**
           ````md
           ```{autolink-preface}
           from dryparse.objects import Command
           ```

           ```
           cmd = Command("test")
           ```
           ````
        **Result:**
           ```{autolink-preface}
           from dryparse.objects import Command
           ```
           ```
           cmd = Command("test")
           ```
        ```

        ```{tab} Wrong
        **Source:**
           ````md
           ```
           cmd = Command("test")
           ```
           ````
        **Result:**
           ```{autolink-skip} next
           ```

           ```
           cmd = Command("test")
           ```
        ```
     ```

     For more info, see the documentation of [sphinx-codeautolink](https://sphinx-codeautolink.readthedocs.io).
