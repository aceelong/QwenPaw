# 数据库表结构

当用户询问数据库相关问题时，使用以下表结构作为参考。如果实际项目有自定义表结构，请在此文件中修改。

{schema_context}

---

## 表命名规范

- 主键字段通常命名为 `id`
- 创建时间字段通常命名为 `created_at`
- 更新时间字段通常命名为 `updated_at`
- 软删除字段通常命名为 `deleted_at` 或 `is_deleted`

## 常用SQL模式

### 分页查询
```sql
SELECT * FROM table_name ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}
```

### 日期范围查询
```sql
SELECT * FROM table_name WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'
```

### 聚合统计
```sql
SELECT DATE(created_at) as date, COUNT(*) as count, SUM(amount) as total
FROM table_name
GROUP BY DATE(created_at)
ORDER BY date DESC
```
