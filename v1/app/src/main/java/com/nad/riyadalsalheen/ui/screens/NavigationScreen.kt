package com.nad.riyadalsalheen.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.vectorResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.nad.riyadalsalheen.R
import com.nad.riyadalsalheen.model.Book
import com.nad.riyadalsalheen.model.Door
import com.nad.riyadalsalheen.model.HadithDetails
import com.nad.riyadalsalheen.ui.components.LoadingContent

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NavigationScreen(
    books: List<Book>,
    doors: List<Door>,
    currentHadith: HadithDetails?,
    onNavigateToDoor: (Int) -> Unit,
    onBackPressed: () -> Unit,
) {
    if (currentHadith == null) {
        return LoadingContent()
    }

    var expandedBookId by remember { mutableIntStateOf(-1) }
    val lazyListState = rememberLazyListState()
    LaunchedEffect(Unit) {
        lazyListState.animateScrollToItem(index = currentHadith.book.id - 1)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("التنقل بين الأبواب", style = MaterialTheme.typography.titleLarge) },
                navigationIcon = {
                    IconButton(onClick = onBackPressed) {
                        Icon(
                            imageVector = ImageVector.vectorResource(id = R.drawable.ic_arrow_back_24),
                            contentDescription = "رجوع"
                        )
                    }
                }
            )
        }
    ) { paddingValues ->
        LazyColumn(
            state = lazyListState,
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(books) { book ->
                NavigationBookItem(
                    book = book,
                    doors = doors.filter { it.bookId == book.id },
                    isExpanded = expandedBookId == book.id,
                    isCurrentBook = currentHadith.book.id == book.id,
                    currentDoorId = currentHadith.door.id,
                    onExpandToggle = {
                        expandedBookId = if (expandedBookId == book.id) -1 else book.id
                    },
                    onDoorClick = onNavigateToDoor
                )
            }
        }
    }
}

@Composable
fun NavigationBookItem(
    book: Book,
    doors: List<Door>,
    isExpanded: Boolean,
    isCurrentBook: Boolean,
    currentDoorId: Int,
    onExpandToggle: () -> Unit,
    onDoorClick: (Int) -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (isCurrentBook)
                MaterialTheme.colorScheme.secondaryContainer else MaterialTheme.colorScheme.surfaceBright
        ),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(
            defaultElevation = if (isCurrentBook) 0.dp else 2.dp
        )
    ) {
        Column {
            // Book Header
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onExpandToggle() }
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = ImageVector.vectorResource(R.drawable.ic_menu_book_24),
                    contentDescription = null,
                    modifier = Modifier.size(24.dp),
                    tint = if (isCurrentBook)
                        MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.onSurfaceVariant
                )

                Spacer(modifier = Modifier.width(12.dp))

                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = book.title,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = if (isCurrentBook) FontWeight.Bold else FontWeight.SemiBold,
                        color = if (isCurrentBook)
                            MaterialTheme.colorScheme.primary
                        else MaterialTheme.colorScheme.onSurface
                    )

                    Text(
                        text = "${doors.size} باب",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Medium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(top = 2.dp)
                    )
                }

                Icon(
                    imageVector = ImageVector.vectorResource(
                        if (isExpanded)
                            R.drawable.ic_expand_less_24
                        else
                            R.drawable.ic_expand_more_24
                    ),
                    contentDescription = null,
                    modifier = Modifier.size(24.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            // Doors List
            AnimatedVisibility(
                visible = isExpanded,
                enter = expandVertically() + fadeIn(),
                exit = shrinkVertically() + fadeOut()
            ) {
                Column {
                    HorizontalDivider(
                        color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.3f)
                    )

                    doors.forEach { door ->
                        NavigationDoorItem(
                            door = door,
                            isSelected = door.id == currentDoorId,
                            onClick = { onDoorClick(door.id) }
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun NavigationDoorItem(
    door: Door,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() }
            .background(
                if (isSelected)
                    MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.3f)
                else Color.Transparent
            )
            .padding(horizontal = 20.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = door.title,
            style = MaterialTheme.typography.titleSmall,
            fontWeight = if (isSelected) FontWeight.SemiBold else FontWeight.Medium,
            color = if (isSelected)
                MaterialTheme.colorScheme.primary
            else MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.weight(1f)
        )

        if (isSelected) {
            Icon(
                imageVector = ImageVector.vectorResource(R.drawable.ic_check_circle_24),
                contentDescription = null,
                modifier = Modifier.size(18.dp),
                tint = MaterialTheme.colorScheme.primary
            )
        }
    }
}
