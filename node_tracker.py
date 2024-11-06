from itertools import chain, tee

nextId = 0


class Tracker:
    def __init__(self, id):
        global nextId

        if id is None:
            self.id = nextId
            nextId += 1
        else:
            self.id = id

        self.stats = []
        self.batchstats = {}
        self.fns = []
        self.classes = []

    def track(self, fn):
        self.batchstats[fn.__name__] = 0

        if fn.__class__ is type:
            self.classes.append(fn)

            class cls(fn):
                def __init__(s, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.batchstats[fn.__name__] += 1

            return cls
        elif callable(fn):
            self.fns.append(fn)

            def afn(*args, **kwargs):
                self.batchstats[fn.__name__] += 1
                return fn(*args, **kwargs)

            return afn

    def tick(self):
        self.stats.append(self.batchstats)
        self.batchstats = dict.fromkeys(
            chain(
                map(lambda fn: fn.__name__, self.fns),
                map(lambda cls: cls.__name__, self.classes),
            ),
            0,
        )

    def dump(
        self, *, dir, fmt="csv", fn_name="calls", cls_name="nodes", batch_name="Gen"
    ):
        fn_file = self._get_file(fmt, dir, fn_name)
        cls_file = self._get_file(fmt, dir, cls_name)

        if fmt == "csv":
            self._write_csv(fn_file, batch_name, map(lambda fn: fn.__name__, self.fns))
            self._write_csv(
                cls_file, batch_name, map(lambda cls: cls.__name__, self.classes)
            )
        elif fmt == "table":
            self._write_table(
                fn_file, batch_name, map(lambda fn: fn.__name__, self.fns)
            )
            self._write_table(
                cls_file, batch_name, map(lambda cls: cls.__name__, self.classes)
            )

    def _get_file(self, fmt, dir, name):
        match fmt:
            case "csv":
                ext = "csv"
            case "table":
                ext = "dump"

        return open(f"{dir}/{self.id}-{name}.{ext}", "w+")

    def _write_csv(self, file, batch_name, names):
        with file:
            (headers, names) = tee(names, 2)

            file.write(",".join(chain([batch_name], headers)))
            file.write("\n")

            for i in range(len(self.stats)):
                batch = self.stats[i]

                (ns, names) = tee(names, 2)
                file.write(
                    ",".join(chain([str(i)], map(lambda name: str(batch[name]), ns)))
                )
                file.write("\n")

    def _write_table(self, file, batch_name, names):
        with file:
            lns = [s for s in map(lambda _: "", chain([()], self.stats))]

            max_batch_len = max(len(str(len(self.stats) + 1)), len(batch_name))
            lns[0] = f"{batch_name:<{max_batch_len}}"
            for i in range(len(self.stats)):
                lns[i + 1] += f"{i:>{max_batch_len}}"
            for name in names:
                max_len = len(name)
                for batch in self.stats:
                    max_len = max(max_len, len(str(batch[name])))
                lns[0] += f" {name:<{max_len}}"
                for i in range(len(self.stats)):
                    lns[i + 1] += f" {self.stats[i][name]:>{max_len}}"

            file.write("\n".join(lns))
