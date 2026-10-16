package com.nad.riyadalsalheen.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.vectorResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nad.riyadalsalheen.R
import com.nad.riyadalsalheen.model.Hadith
import com.nad.riyadalsalheen.ui.viewmodel.MainViewModel

@Composable
fun BookmarksScreen(
    viewModel: MainViewModel,
    onHadithSelected: (Int) -> Unit,
    onBackPressed: () -> Unit
)
{
    BookmarksScreenContent(
        bookmarks = viewModel.bookmarks.value,
        onHadithSelected = onHadithSelected,
        onRemoveBookmark = { hadithId ->
            viewModel.toggleBookmark(hadithId = hadithId)
        },
        onBackPressed = onBackPressed
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BookmarksScreenContent(
    bookmarks: List<Hadith>,
    onHadithSelected: (Int) -> Unit = {},
    onRemoveBookmark: (Int) -> Unit = {},
    onBackPressed: () -> Unit = {}
)
{
    Scaffold(
        topBar = {
            TopAppBar(
                expandedHeight = 80.dp,
                title = {
                    Column {
                        Text(
                            text = "المفضلة",
                            style = MaterialTheme.typography.titleLarge,
                            color = MaterialTheme.colorScheme.onSurface,
                            fontWeight = FontWeight.Bold
                        )
                        if (bookmarks.isNotEmpty()) {
                            Text(
                                text = "${bookmarks.size} حديث",
                                style = MaterialTheme.typography.titleSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                fontWeight = FontWeight.SemiBold
                            )
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBackPressed) {
                        Icon(
                            imageVector = ImageVector.vectorResource(id = R.drawable.ic_arrow_back_24),
                            contentDescription = "رجوع"
                        )
                    }
                },
                actions = {
                    if (bookmarks.isNotEmpty()) {
                        var showClearDialog by remember { mutableStateOf(false) }

                        IconButton(onClick = { showClearDialog = true }) {
                            Icon(
                                imageVector = ImageVector.vectorResource(id = R.drawable.ic_delete_sweep_24),
                                contentDescription = "مسح الكل"
                            )
                        }

                        if (showClearDialog) {
                            AlertDialog(
                                onDismissRequest = { showClearDialog = false },
                                title = { Text("مسح جميع المفضلات", style = MaterialTheme.typography.titleLarge) },
                                text = { Text("هل أنت متأكد من مسح جميع الأحاديث المفضلة؟", style = MaterialTheme.typography.bodyMedium) },
                                confirmButton = {
                                    TextButton(
                                        onClick = {
                                            bookmarks.forEach { hadith ->
                                                onRemoveBookmark(hadith.id)
                                            }
                                            showClearDialog = false
                                        }
                                    ) {
                                        Text("مسح", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.error)
                                    }
                                },
                                dismissButton = {
                                    TextButton(onClick = { showClearDialog = false }) {
                                        Text("إلغاء", style = MaterialTheme.typography.labelLarge)
                                    }
                                }
                            )
                        }
                    }
                }
            )
        }
    )
    { paddingValues ->
        if (bookmarks.isEmpty()) {
            // Empty state
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier.padding(32.dp)
                ) {
                    Icon(
                        imageVector = ImageVector.vectorResource(id = R.drawable.ic_bookmark_24),
                        contentDescription = null,
                        modifier = Modifier.size(80.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "لا توجد أحاديث مفضلة",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "اضغط على أيقونة المفضلة في صفحة الحديث لإضافته هنا",
                        style = MaterialTheme.typography.bodyMedium,
                        textAlign = TextAlign.Center,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(
                    items = bookmarks,
                    key = { it.id }
                ) { hadith ->
                    BookmarkItem(
                        hadith = hadith,
                        onItemClick = { onHadithSelected(hadith.id) },
                        onRemoveBookmark = { onRemoveBookmark(hadith.id) }
                    )
                }
            }
        }
    }
}

@Composable
fun BookmarkItem(
    hadith: Hadith,
    onItemClick: () -> Unit,
    onRemoveBookmark: () -> Unit
) {
    var showRemoveDialog by remember { mutableStateOf(false) }

    Card(
        onClick = onItemClick,
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.Top
        ) {
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = "الحديث ${hadith.id}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        text = hadith.title,
                        style = MaterialTheme.typography.titleSmall,
                        modifier = Modifier.weight(1f),
                        textAlign = TextAlign.End,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                val cleanHadithText = hadith.matn.replace(Regex("<[^>]*>"), "")
                val displayText = if (cleanHadithText.length > 150) {
                    cleanHadithText.substring(0, 150) + "..."
                } else {
                    cleanHadithText
                }

                Text(
                    text = displayText,
                    style = MaterialTheme.typography.bodyMedium,
                    lineHeight = 22.sp,
                    maxLines = 3,
                    overflow = TextOverflow.Ellipsis,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            IconButton(
                onClick = { showRemoveDialog = true },
                modifier = Modifier.padding(start = 8.dp)
            ) {
                Icon(
                    imageVector = ImageVector.vectorResource(id = R.drawable.ic_bookmark_remove_24),
                    contentDescription = "إزالة من المفضلة",
                    tint = MaterialTheme.colorScheme.error.copy(alpha = 0.7f)
                )
            }
        }
    }

    if (showRemoveDialog) {
        AlertDialog(
            onDismissRequest = { showRemoveDialog = false },
            title = { Text("إزالة من المفضلة", style = MaterialTheme.typography.titleLarge) },
            text = { Text("هل تريد إزالة هذا الحديث من المفضلة؟", style = MaterialTheme.typography.bodyMedium) },
            confirmButton = {
                TextButton(
                    onClick = {
                        onRemoveBookmark()
                        showRemoveDialog = false
                    }
                ) {
                    Text("إزالة", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.error)
                }
            },
            dismissButton = {
                TextButton(onClick = { showRemoveDialog = false }) {
                    Text("إلغاء", style = MaterialTheme.typography.labelLarge)
                }
            }
        )
    }
}