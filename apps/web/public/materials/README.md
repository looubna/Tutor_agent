# Lesson materials

Put lesson PDFs in here, grouped by subject:

```
public/materials/
  english/a1-names-and-greetings.pdf
  german/b1-cases.pdf
  physics/adv-oscillations.pdf
```

Then point the lesson at it in `src/lib/curriculum.ts`. A lesson can be written
as a bare title, or as an object when it needs more:

```ts
ch("intro", "I can introduce myself and others", [
  {
    id: "l1",
    title: "Names and greetings",
    category: "Vocabulary",
    summary: "In this lesson you'll learn how to say hello and goodbye.",
    objectives: ["I can greet people in a classroom.", "I can say goodbye."],
    material: "/materials/english/a1-names-and-greetings.pdf",
  },
  "Countries and nationalities",   // still fine as a plain title
]),
```

`material` is the path as the browser sees it — everything under `public/` is
served from `/`. A lesson without `material` shows "No material has been
attached to this lesson yet" instead of a dead button.

**One caveat:** anything in `public/` is served to anyone who knows the URL,
signed in or not. That is fine for open handouts. If materials should be
restricted to enrolled learners, they need to move out of `public/` and behind
an authenticated route.
