<!DOCTYPE html>
<head>
    <title>Sorting Tables w/ Javascript</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
    <!-- <link rel="stylesheet" href="./src/style.css"> -->
    <style>
        * {
            margin: 0;
            padding: 0;

            box-sizing: border-box;
            font-family: sans-serif;
        }

        /* Add alternating row colors */
        tr:nth-of-type(2n) {
            background: rgba(0 0 0 / 0.1);
        };

        /* Add pointer to currently sorted column */
        .table-sortable th {
            cursor: pointer;
        }

        /* Up arrow */
        .table-sortable .th-sort-asc::after {
            content: "\25b4";
        }

        /* Down arrow */
        .table-sortable .th-sort-desc::after {
            content: "\25be";
        }

        /* Add space between text and arrow */
        .table-sortable .th-sort-asc::after,
        .table-sortable .th-sort-desc::after {
            margin-left: 5px;
        }

        /* Add overlay to currently sorted column header */
        .table-sortable .th-sort-asc, 
        .table-sortable .th-sort-desc {
            background: rgba(200 2 2 / 0.75);
        }
		
		/* Body */
		body {
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
		
		main.table {
            width: 82vw;
            height: 90vh;
			
            border-radius: .8rem;

            overflow: hidden;
        }
		
		.table__header {
            width: 100%;
            height: 10%;
            padding: .8rem 1rem;

            display: flex;
            justify-content: space-between;
            align-items: center;
        }
		
		.table__body {
            width: 100%;
            max-height: calc(150% - 1.6rem);

            margin: .8rem auto;
            border-radius: .6rem;

            overflow: auto;
            overflow: overlay;
        }
		
		/* TABLE OVERFLOW SIZING */
/* 		.table__body { overflow-x: scroll; } */
		th, td { min-width: 200px; }
		
		/* STICKY HEADER */
		thead th {
            position: sticky;
            top: 0;
            left: 0;
            cursor: pointer;
            text-transform: capitalize;
            background: rgba(200 2 2 / 1);
        }
		
		/* ANIMATION EFFECTS */
		tbody tr {
            --delay: .1s;
        }
		
		tbody tr.hide {
            opacity: 0;
            transform: translateX(100%);
        }

        tbody tr:hover {
            background: rgba(0 0 0 / 0.2);
        }

        tbody tr td,
        tbody tr td p,
        tbody tr td img {
            transition: .2s ease-in-out;
        }

        tbody tr.hide td,
        tbody tr.hide td p {
            padding: 0;
            font: 0 / 0 sans-serif;
            transition: .2s ease-in-out .5s;
        }
    </style>
</head>

<body>
    
    <main class="table">
        <section class="table__body">
            <table class="table table-sortable">
                <thead>
                    <tr>
                        <?php
                        global $wpdb;
                        $columns = $wpdb->get_results("SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME= N'ddoloot_named_items' AND COLUMN_NAME != 'id'");
                        echo '<tr>';

                        foreach ($columns as $column) {
                            echo '<th>' . $column->column_name . '</th>';
                        }
                        echo '</tr>';
                        ?>
                    </tr>
                </thead>
                <tbody>
                    <?php
                    global $wpdb;
                    $rows = $wpdb->get_results("SELECT * FROM ddoloot_named_items");
                    
                    foreach ($rows as $row) {
                        echo '<tr>';
						foreach ($columns as $column) {
							$column_name = $column->column_name;
							$string = $row->$column_name;
							$string = str_replace("'", '"', $string);
                            $array = json_decode($string);
							if (is_array($array)) {
								echo '<td data-cell="' . $column_name . '"><ul>';
								foreach ($array as $item) {
									echo '<li>' . $item . '</li>';
								}
								echo '</ul></td>';
							} else {
								echo '<td data-cell="' . $column->column_name . '">' . $row->$column_name . '</td>';
							}
						}
                        echo '</tr>';
                    }
                    ?>
                </tbody>
            </table>
        </section>
    </main>
    <script>
        /**
         * Sorts a HTML table
         * 
         * @param {HTMLTableElement} table The table to sort
         * @param {number} column The index of the column to sort
         * @param {boolean} asc Determines if the sorting will be in ascending order
         */

        function sortTableByColumn(table, column, asc = true) {
            const dirModifier = asc ?  1 : -1;
            const tBody = table.tBodies[0];
            const rows = Array.from(tBody.querySelectorAll("tr"));

            // Sort each row
            const sortedRows = rows.sort((a, b) => {
                const aColText = a.querySelector(`td:nth-child(${ column + 1 })`).textContent.trim();
                const bColText = b.querySelector(`td:nth-child(${ column + 1 })`).textContent.trim();

                return aColText > bColText ? (1 * dirModifier) : (-1 * dirModifier);
            });

            // Remove all existing TRs from the table
            while (tBody.firstChild) {
                tBody.removeChild(tBody.firstChild);
            }

            // Re-add the newly sorted rows
            tBody.append(...sortedRows);

            // Remember how the column is currently sorted
            table.querySelectorAll("th").forEach(th => th.classList.remove("th-sort-asc", "th-sort-desc"));
            table.querySelector(`th:nth-child(${ column + 1})`).classList.toggle("th-sort-asc", asc);
            table.querySelector(`th:nth-child(${ column + 1})`).classList.toggle("th-sort-desc", !asc);
        }

        document.querySelectorAll(".table-sortable th").forEach(headerCell => {
            headerCell.addEventListener("click", () => {
                const tableElement = headerCell.parentElement.parentElement.parentElement;
                const headerIndex = Array.prototype.indexOf.call(headerCell.parentElement.children, headerCell);
                const currentIsAscending = headerCell.classList.contains("th-sort-asc");

                sortTableByColumn(tableElement, headerIndex, !currentIsAscending);
            });
        });
    </script>
</body>