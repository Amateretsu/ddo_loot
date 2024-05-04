global $wpdb;
$result = $wpdb->get_results("SELECT * FROM ddoloot_named_items");

echo '<input type="text" id="myInput" onkeyup="myFunction()" placeholder="Search for names.." title="Type in a name">';

echo '<div class="table_container"> <table>';
echo '<tr><th>Item Name</th><th>Item Type</th><th>Minimum Level</th></tr>';
foreach ($result as $row) {
	echo "<tr><td>" . $row->item_name . "</td><td>" . $row->item_type . "</td><td>" . $row->minimum_level . "</tr>";
}
echo "</table></div>";
	
