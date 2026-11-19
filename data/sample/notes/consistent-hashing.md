---
title: Consistent hashing
tags: [systems]
source: https://en.wikipedia.org/wiki/Consistent_hashing
---

# Consistent hashing

In computer science, consistent hashing is a special kind of hashing technique such that when a hash table is resized, only keys need to be remapped on average where is the number of keys and is the number of slots. Consistent hashing evenly distributes cache keys across shards, even if some of the shards crash or become unavailable. In contrast, in most traditional hash tables, a change in the number of array slots causes nearly all keys to be remapped because the mapping between the keys and the slots is defined by a modular operation.
