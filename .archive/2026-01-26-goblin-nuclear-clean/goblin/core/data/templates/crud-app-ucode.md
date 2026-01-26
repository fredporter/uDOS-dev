---
title: CRUD Task Manager
version: 2.0.0
author: uDOS
created: 2026-01-06
tags: [crud, tasks, data, template]
description: Create, Read, Update, Delete operations for task management
permissions:
  execute: true
  save_state: true
variables:
  tasks: []
  task_count: 0
  running: true
---

# CRUD Task Manager

A template demonstrating Create, Read, Update, Delete (CRUD) operations with a simple task list.

---

## Initialize

Set up the task list and state variables.

```upy
# Initialize task list
tasks = []
task_count = 0
running = True

PRINT "=========================================="
PRINT "  Task Manager"
PRINT "=========================================="
```

---

## Main Menu

The main interaction loop with CRUD options.

```upy
LABEL MENU

IF NOT running:
    END

PRINT ""
CHOICE "Choose an action:"
    OPTION "Create Task" -> CREATE
    OPTION "View Tasks" -> READ
    OPTION "Update Task" -> UPDATE
    OPTION "Delete Task" -> DELETE
    OPTION "Exit" -> EXIT
END
```

---

## Create Task

Add a new task to the list.

```upy
LABEL CREATE

PRINT ""
PRINT "Create New Task"
PRINT "=========================================="

task_desc = INPUT "Enter task description:"

IF task_desc == "":
    PRINT "Task cannot be empty!"
    GOTO MENU

task_count = task_count + 1
tasks.append(str(task_count) + ". " + task_desc)
PRINT "✅ Task created successfully!"

GOTO MENU
```

---

## View Tasks

Display all tasks in the list.

```upy
LABEL READ

PRINT ""
PRINT "All Tasks"
PRINT "=========================================="

IF task_count == 0:
    PRINT "No tasks found."
ELSE:
    FOR task IN tasks:
        PRINT task

PRINT ""
INPUT "Press ENTER to continue"

GOTO MENU
```

---

## Update Task

Modify an existing task.

```upy
LABEL UPDATE

PRINT ""
PRINT "Update Task"
PRINT "=========================================="

IF task_count == 0:
    PRINT "No tasks to update."
    GOTO MENU

# Show current tasks
FOR task IN tasks:
    PRINT task

PRINT ""
task_num = INT(INPUT "Enter task number to update:")

IF task_num < 1 OR task_num > task_count:
    PRINT "Invalid task number!"
    GOTO MENU

new_desc = INPUT "Enter new description:"

IF new_desc == "":
    PRINT "Description cannot be empty!"
    GOTO MENU

tasks[task_num - 1] = str(task_num) + ". " + new_desc
PRINT "✅ Task updated successfully!"

GOTO MENU
```

---

## Delete Task

Remove a task from the list.

```upy
LABEL DELETE

PRINT ""
PRINT "Delete Task"
PRINT "=========================================="

IF task_count == 0:
    PRINT "No tasks to delete."
    GOTO MENU

# Show current tasks
FOR task IN tasks:
    PRINT task

PRINT ""
task_num = INT(INPUT "Enter task number to delete:")

IF task_num < 1 OR task_num > task_count:
    PRINT "Invalid task number!"
    GOTO MENU

tasks.pop(task_num - 1)
task_count = task_count - 1

# Renumber remaining tasks
FOR i IN RANGE(LEN(tasks)):
    parts = tasks[i].split(". ", 1)
    IF LEN(parts) > 1:
        tasks[i] = str(i + 1) + ". " + parts[1]

PRINT "✅ Task deleted successfully!"

GOTO MENU
```

---

## Exit

Clean exit from the application.

```upy
LABEL EXIT

running = False
PRINT ""
PRINT "Goodbye!"

END
```

---

## Notes

This template demonstrates:

- **CRUD Operations**: Create, Read, Update, Delete patterns
- **Lists**: Dynamic array with append, pop, indexing
- **Loops**: FOR iteration over collections
- **Input Validation**: Checking for empty strings and valid indices
- **State Management**: Using variables to track application state

### Customization Ideas

1. Add task priorities (high/medium/low)
2. Add due dates with date validation
3. Add task categories or tags
4. Add search/filter functionality
5. Persist tasks to a file
