# DB-Query-Client

<p>
<a href="https://github.com/colley/dbquery-client"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/colley/dbquery-client?style=social"/></a>
<a href="https://marketplace.dify.ai/plugins/colley/dbquery-client"><img alt="Dify Marketplace" src="https://img.shields.io/badge/Dify%20Marketplace-dbquery-client"/></a>
</p>

[简体中文](./README_CN.md) | **English**  

[DB-Query-Client](https://github.com/colley/dbquery-client) is a plugin tool designed for Dify workflows, providing database operation nodes. It currently supports Mysql、Clickhouse databases.

![DB-Query-Client demo](imags/dbcn-demo_en.png)

## Features
- Securely manages database connection information through Dify’s `credentials_for_provider` mechanism.
- Supports parameterized execution of DML statements such as `SELECT` not  supports `INSERT` or `DELETE`.
- Provides dynamic SQL generation with conditional logic support.

## Installation
To use `DB-Query-Client` in a Dify workflow:
1. Install the plugin via the Dify plugin [marketplace](https://marketplace.dify.ai/plugins/colley/dbquery-client) or manually download version from the [release page](https://github.com/colley/dbquery-client/releases).
2. Configure Mysql/Clickhouse credentials in Dify’s `Plugins -> Authorization` settings.

![DB-Query-Client credential demo](imags/dbcn-auth-demo.png)

## Node Output
### Query Execution
For `SELECT` statements, the node provides the following return values:
- **`data`**: The query result data, represented as a list of rows where each row is an array of column values.
- **`columns`**: A list of column names corresponding to the result set.
- **`json[0].data`**: An alternative representation of the query result data in the default `json` return format of the plugin tool, structured as an object with column names as keys.

**Example Output:**
```json
{
    "data": [
        ["row0_value0", "row0_value1", "row0_value2"],
        ["row1_value0", "row1_value1", "row1_value2"],
        ["row2_value0", "row2_value1", "row2_value2"]
    ],
    "columns": ["column0", "column1", "column2"],
    "json": [
        {
            "data": [
                {
                    "column0": "value0",
                    "column1": "value1",
                    "column2": "value2"
                }
            ]
        }
    ]
}
```

### Update Execution not Supports
For `INSERT`, `UPDATE`, or `DELETE` statements, the node returns:
- **`affected_rows`**: The number of rows affected.

**Example Output:**
```json
{
    "affected_rows": 2
}
```

## Limitations
- Currently supports only Mysql/Clickhouse databases.
- Dynamic SQL relies on Jinja2 syntax, which may require familiarity with templating.

## Contribution Guidelines
Contributions are welcome! To participate:
1. Fork this repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Submit a Pull Request.

Please ensure your code adheres to the project’s style guidelines and includes appropriate tests.

## License
This project is released under the Apache License 2.0. See the `LICENSE` file for details.

## Contact
For questions or support, please submit an issue in the repository.
