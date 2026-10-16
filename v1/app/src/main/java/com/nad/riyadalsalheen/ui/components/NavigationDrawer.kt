package com.nad.riyadalsalheen.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.vectorResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.nad.riyadalsalheen.R
import com.nad.riyadalsalheen.model.Hadith
import com.nad.riyadalsalheen.ui.theme.LocalDarkTheme

@Composable
fun NavigationDrawer(
    bookmarks: List<Hadith>,
    hadithCount: Int,
    versionName: String,
    onNavigateToBookmarks: () -> Unit = {},
    onNavigateToHadith: (Int) -> Unit = {},
    onNavigateToAbout: () -> Unit = {},
    onNavigateToNavigation: () -> Unit = {},
    onFontSizeChange: () -> Unit = {},
    onToggleDarkMode: () -> Unit = {},
    onClose: () -> Unit = {}
) {
    val isDarkMode = LocalDarkTheme.current
    ModalDrawerSheet(
        modifier = Modifier.fillMaxWidth(0.85f),
        drawerContainerColor = MaterialTheme.colorScheme.surface
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 20.dp)
        ) {
            // Header
            Row(
                modifier = Modifier
                    .padding(top = 20.dp, bottom = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = "رياض الصالحين",
                        style = MaterialTheme.typography.headlineMedium,
                        color = MaterialTheme.colorScheme.onSurface,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "$hadithCount حديث",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }

                Column(
                    horizontalAlignment = Alignment.End
                ) {
                    IconButton(onClick = onToggleDarkMode) {
                        Icon(
                            imageVector = ImageVector.vectorResource(
                                if (isDarkMode) R.drawable.ic_dark_mode_24
                                else R.drawable.ic_light_mode_24
                            ),
                            contentDescription = if (isDarkMode) "Switch to Light Mode"
                            else "Switch to Dark Mode",
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    IconButton(onClick = {
                        onFontSizeChange()
                        onClose()
                    }) {
                        Icon(
                            imageVector = ImageVector.vectorResource(R.drawable.ic_text_fields_24),
                            contentDescription = "حجم الخط",
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            HorizontalDivider(
                modifier = Modifier.padding(vertical = 8.dp),
                color = MaterialTheme.colorScheme.outlineVariant
            )

            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                contentPadding = PaddingValues(bottom = 8.dp)
            ) {
                item {
                    DrawerMenuItem(
                        text = "التنقل بين الأبواب",
                        icon = ImageVector.vectorResource(R.drawable.ic_door_front_24),
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.clickable {
                            onNavigateToNavigation()
                            onClose()
                        }
                    )
                }

                // Divider
                item {
                    HorizontalDivider(
                        modifier = Modifier.padding(vertical = 8.dp),
                        color = MaterialTheme.colorScheme.outlineVariant
                    )
                }

                // Bookmarks Section Header
                item {
                    DrawerMenuItem(
                        text = "المفضلة",
                        icon = ImageVector.vectorResource(R.drawable.ic_bookmark_24),
                        fontWeight = FontWeight.SemiBold
                    )
                }

                // Show message if no bookmarks
                if (bookmarks.isEmpty()) {
                    item {
                        Text(
                            text = "لا توجد مفضلة",
                        )
                    }
                }
                // View All Bookmarks (only show if there are bookmarks)
                else {
                    // Recent Bookmarks
                    items(bookmarks.take(3)) { bookmark ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(start = 0.dp, end = 12.dp, top = 8.dp, bottom = 8.dp)
                                .clickable {
                                    onNavigateToHadith(bookmark.id)
                                    onClose()
                                },
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "${bookmark.id}",
                                style = MaterialTheme.typography.bodyLarge,
                                fontWeight = FontWeight.SemiBold,
                                color = MaterialTheme.colorScheme.primary,
                                textAlign = TextAlign.End,
                                modifier = Modifier.width(40.dp)
                            )
                            Spacer(modifier = Modifier.width(12.dp))
                            Text(
                                text = bookmark.title,
                                style = MaterialTheme.typography.bodyLarge,
                                fontWeight = FontWeight.SemiBold,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                        }
                    }

                    item {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .heightIn(min = 48.dp)
                                .clickable {
                                    onNavigateToBookmarks()
                                    onClose()
                                }
                                .padding(start = 24.dp, end = 12.dp, top = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = ImageVector.vectorResource(R.drawable.ic_arrow_forward_24),
                                contentDescription = null,
                                modifier = Modifier.size(20.dp),
                                tint = MaterialTheme.colorScheme.primary
                            )
                            Spacer(modifier = Modifier.width(12.dp))
                            Text(
                                text = "عرض جميع المفضلة",
                                style = MaterialTheme.typography.bodyLarge,
                                fontWeight = FontWeight.Medium,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                }

                // Divider
                item {
                    HorizontalDivider(
                        modifier = Modifier.padding(vertical = 8.dp),
                        color = MaterialTheme.colorScheme.outlineVariant
                    )
                }

                // About
                item {
                    DrawerMenuItem(
                        text = "حول التطبيق",
                        icon = ImageVector.vectorResource(R.drawable.ic_info_24),
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.clickable {
                            onNavigateToAbout()
                            onClose()
                        }
                    )
                }
            }

            // Footer with version
            HorizontalDivider(
                modifier = Modifier.padding(vertical = 8.dp),
                color = MaterialTheme.colorScheme.outlineVariant
            )

            Text(
                text = "الإصدار $versionName",
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Normal,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 16.dp),
                textAlign = TextAlign.Center
            )
        }
    }
}


// Replace DrawerMenuItem function:
@Composable
fun DrawerMenuItem(
    text: String,
    icon: ImageVector,
    modifier: Modifier = Modifier,
    fontWeight: FontWeight = FontWeight.SemiBold
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 48.dp)
            .padding(top = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            modifier = Modifier.size(24.dp),
            tint = MaterialTheme.colorScheme.onSurface
        )
        Spacer(modifier = Modifier.width(12.dp))
        Text(
            text = text,
            style = MaterialTheme.typography.titleLarge,
            fontWeight = fontWeight,
            color = MaterialTheme.colorScheme.onSurface,
        )
    }
}