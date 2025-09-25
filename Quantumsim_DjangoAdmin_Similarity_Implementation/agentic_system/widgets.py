from django import forms
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe


class UserTableWidget(forms.Widget):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        
    def format_value(self, value):
        if value is None:
            return []
        if hasattr(value, 'all'):
            return [user.id for user in value.all()]
        return value
    
    def render(self, name, value, attrs=None, renderer=None):
        selected_ids = self.format_value(value) or []
        all_users = User.objects.all().order_by('username')
        
        html = f'''
        <div style="display: flex; gap: 20px;">
            <div style="flex: 1;">
                <div class="user-table-container" style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd;">
                    <table class="user-table" style="width: 100%; border-collapse: collapse;">
                        <thead style="background-color: #f8f9fa; position: sticky; top: 0;">
                            <tr>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">
                                    <input type="checkbox" id="select-all-users"> Select All
                                </th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;" data-column="0">Username</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;" data-column="1">Email</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;" data-column="2">First Name</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;" data-column="3">Last Name</th>
                            </tr>
                        </thead>
                        <tbody>
        '''
        
        for user in all_users:
            checked = 'checked' if user.id in selected_ids else ''
            html += f'''
                        <tr class="user-row">
                            <td style="padding: 8px; border: 1px solid #ddd;">
                                <input type="checkbox" name="{name}" value="{user.id}" {checked} class="user-checkbox">
                            </td>
                            <td style="padding: 8px; border: 1px solid #ddd;" data-column="0">{user.username}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;" data-column="1">{user.email or ''}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;" data-column="2">{user.first_name or ''}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;" data-column="3">{user.last_name or ''}</td>
                        </tr>
            '''
        
        html += f'''
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="column-selector-panel" style="width: 350px; padding: 20px; background: #f8f9fa; border: 1px solid #ddd;">
            <h3 style="margin: 0 0 15px 0; font-weight: 500; color: black;">Filters</h3>
            <div id="user-filters-container">
                <div class="filter-row" style="display: flex; gap: 5px; margin-bottom: 10px; align-items: center;">
                    <select class="filter-column" style="padding: 4px;">
                        <option value="">Column</option>
                        <option value="0">Username</option>
                        <option value="1">Email</option>
                        <option value="2">First Name</option>
                        <option value="3">Last Name</option>
                    </select>
                    <select class="filter-operator" style="padding: 4px;">
                        <option value="include">Include</option>
                        <option value="exclude">Exclude</option>
                        <option value="empty">Is Empty</option>
                        <option value="not_empty">Not Empty</option>
                    </select>
                    <input type="text" class="filter-value" placeholder="Value" style="padding: 4px; width: 80px; min-width: 60px;" />
                    <button type="button" class="add-filter-btn" style="padding: 4px 8px; background: #035289; color: white; border: none; cursor: pointer;">+</button>
                </div>
            </div>

            <div style="margin: 15px 0; font-weight: 500; color: black;">Column Selection</div>
            <div class="column-checkboxes" style="display: flex; flex-direction: column; gap: 5px;">
                <label style="display: flex; align-items: center; gap: 5px;">
                    <input type="checkbox" id="select-all-columns" checked />
                    Select All
                </label>
                <label style="display: flex; align-items: center; gap: 5px;">
                    <input type="checkbox" class="column-toggle" data-column="0" checked />
                    Username
                </label>
                <label style="display: flex; align-items: center; gap: 5px;">
                    <input type="checkbox" class="column-toggle" data-column="1" checked />
                    Email
                </label>
                <label style="display: flex; align-items: center; gap: 5px;">
                    <input type="checkbox" class="column-toggle" data-column="2" checked />
                    First Name
                </label>
                <label style="display: flex; align-items: center; gap: 5px;">
                    <input type="checkbox" class="column-toggle" data-column="3" checked />
                    Last Name
                </label>
            </div>

            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button type="button" id="reset-user-filters" style="padding: 8px 12px; background: #6c757d; color: white; border: none; cursor: pointer; flex: 1;">RESET</button>
                <button type="button" id="apply-user-filters" style="padding: 8px 12px; background: #035289; color: white; border: none; cursor: pointer; flex: 1;">APPLY</button>
            </div>
        </div>
    </div>
        
        <script>
        (function() {{
            const selectAllCheckbox = document.getElementById('select-all-users');
            const userCheckboxes = document.querySelectorAll('.user-checkbox');
            const userRows = document.querySelectorAll('.user-row');
            const table = document.querySelector('.user-table');
            let activeFilters = [];
            
            // Column visibility
            document.querySelectorAll('.column-toggle').forEach(toggle => {{
                toggle.addEventListener('change', function() {{
                    const column = this.dataset.column;
                    const isVisible = this.checked;
                    
                    // Toggle header
                    const header = table.querySelector(`th[data-column="${{column}}"]`);
                    if (header) header.style.display = isVisible ? '' : 'none';
                    
                    // Toggle cells
                    table.querySelectorAll(`td[data-column="${{column}}"]`).forEach(cell => {{
                        cell.style.display = isVisible ? '' : 'none';
                    }});
                }});
            }});
            
            // Select all columns
            document.getElementById('select-all-columns').addEventListener('change', function() {{
                document.querySelectorAll('.column-toggle').forEach(toggle => {{
                    toggle.checked = this.checked;
                    toggle.dispatchEvent(new Event('change'));
                }});
            }});
            
            // Add filter
            document.querySelector('.add-filter-btn').addEventListener('click', function() {{
                const column = document.querySelector('.filter-column').value;
                const operator = document.querySelector('.filter-operator').value;
                const value = document.querySelector('.filter-value').value;
                
                if (column) {{
                    activeFilters.push({{ column, operator, value }});
                    applyFilters();
                    document.querySelector('.filter-value').value = '';
                }}
            }});
            
            // Apply filters
            function applyFilters() {{
                userRows.forEach(row => {{
                    let visible = true;
                    
                    activeFilters.forEach(filter => {{
                        const cell = row.querySelector(`td[data-column="${{filter.column}}"]`);
                        if (!cell) return;
                        
                        const cellText = cell.textContent.toLowerCase();
                        const filterValue = filter.value.toLowerCase();
                        
                        switch (filter.operator) {{
                            case 'include':
                                if (filterValue && !cellText.includes(filterValue)) visible = false;
                                break;
                            case 'exclude':
                                if (filterValue && cellText.includes(filterValue)) visible = false;
                                break;
                            case 'empty':
                                if (cellText.trim() !== '') visible = false;
                                break;
                            case 'not_empty':
                                if (cellText.trim() === '') visible = false;
                                break;
                        }}
                    }});
                    
                    row.style.display = visible ? '' : 'none';
                }});
            }}
            
            // Reset filters
            document.getElementById('reset-user-filters').addEventListener('click', function() {{
                activeFilters = [];
                userRows.forEach(row => row.style.display = '');
                document.querySelector('.filter-column').value = '';
                document.querySelector('.filter-operator').value = 'include';
                document.querySelector('.filter-value').value = '';
            }});
            
            // Apply button
            document.getElementById('apply-user-filters').addEventListener('click', function() {{
                const column = document.querySelector('.filter-column').value;
                const operator = document.querySelector('.filter-operator').value;
                const value = document.querySelector('.filter-value').value;
                
                if (column) {{
                    activeFilters.push({{ column, operator, value }});
                    applyFilters();
                }}
            }});
            
            // Select all functionality
            selectAllCheckbox.addEventListener('change', function() {{
                const visibleCheckboxes = Array.from(userCheckboxes).filter(cb => 
                    cb.closest('.user-row').style.display !== 'none'
                );
                visibleCheckboxes.forEach(cb => cb.checked = this.checked);
            }});
            
            // Update select all when individual checkboxes change
            userCheckboxes.forEach(cb => {{
                cb.addEventListener('change', function() {{
                    const visibleCheckboxes = Array.from(userCheckboxes).filter(cb => 
                        cb.closest('.user-row').style.display !== 'none'
                    );
                    const checkedVisible = visibleCheckboxes.filter(cb => cb.checked);
                    selectAllCheckbox.checked = checkedVisible.length === visibleCheckboxes.length;
                    selectAllCheckbox.indeterminate = checkedVisible.length > 0 && checkedVisible.length < visibleCheckboxes.length;
                }});
            }});
        }})();
        </script>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        return data.getlist(name)